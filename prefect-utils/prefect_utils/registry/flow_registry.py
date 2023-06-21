import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from prefect import Flow, flow, get_client
from prefect.client.schemas.actions import WorkPoolCreate
from prefect.deployments import Deployment, run_deployment
from prefect.exceptions import ObjectNotFound
from prefect.infrastructure.kubernetes import KubernetesJob, KubernetesManifest
from prefect.server.schemas.filters import DeploymentFilter, DeploymentFilterTags
from prefect.server.schemas.schedules import SCHEDULE_TYPES

from prefect_utils.registry.decorators import datadog_event

DEFAULT_CONCURRENCY_LIMIT = int(os.getenv("FLOW_RUN_DEFAULT_CONCURRENCY_LIMIT", "10"))

logger = logging.getLogger(__name__)


@dataclass
class DeploymentInfo:
    name: str
    concurrency_limit: Optional[int] = None
    schedule: Optional[SCHEDULE_TYPES] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    tags: Optional[list[str]] = None

    async def run_deployment(
        self,
        flow_fn: Flow,
        parameters: Optional[dict] = None,
    ) -> str:
        deployment_name = "%s/%s" % (
            flow_fn.__name__.replace("_", "-"),
            self.name,
        )
        flow_run = await run_deployment(
            name=deployment_name,
            timeout=0,
            parameters=parameters,
        )
        return str(flow_run.id)


@dataclass
class FlowInfo:
    flow: Flow
    deployments: list[DeploymentInfo]

    async def get_deployments(
        self,
        work_pool_name,
        manifest: KubernetesManifest,
        namespace: str,
        tags=list[str],
    ) -> list[Deployment]:
        prefect_deployments = []
        flow_path = os.getenv("PREFECT_FLOW_DIR", None)
        for deployment_info in self.deployments:
            manifest_cp = manifest.copy()
            manifest_cp["spec"]["template"]["metadata"]["labels"][
                "prefect.io/deployment_name"
            ] = deployment_info.name
            manifest_cp["spec"]["template"]["metadata"]["labels"][
                "prefect.io/flow"
            ] = self.flow.name
            manifest_cp["metadata"]["labels"][
                "prefect.io/deployment_name"
            ] = deployment_info.name
            manifest_cp["metadata"]["labels"]["prefect.io/flow"] = self.flow.name
            infra = KubernetesJob(
                job=manifest,
                namespace=namespace,
                pod_watch_timeout_seconds=60 * 10,
            )
            deployment: Deployment = await Deployment.build_from_flow(
                flow=self.flow,
                name=deployment_info.name,
                work_pool_name=work_pool_name,
                work_queue_name=deployment_info.name,
                infrastructure=infra,
                schedule=deployment_info.schedule,
                parameters=deployment_info.parameters,
                path=flow_path,
            )
            prefect_deployments.append(deployment)
        return prefect_deployments


async def create_work_pool_if_not_exists(work_pool_name):
    async with get_client() as client:
        try:
            await client.read_work_pool(work_pool_name)
            return
        except ObjectNotFound:
            pass
        cr = WorkPoolCreate(
            name=work_pool_name,
        )
        await client.create_work_pool(cr)


async def update_or_create_work_queue(
    work_queue_name: str, work_pool_name: str, concurrency_limit: Optional[int] = None
):
    concurrency_limit = (
        min(concurrency_limit, DEFAULT_CONCURRENCY_LIMIT)
        if concurrency_limit is not None
        else DEFAULT_CONCURRENCY_LIMIT
    )
    async with get_client() as client:
        try:
            work_queue = await client.read_work_queue_by_name(
                work_queue_name, work_pool_name
            )
            await client.update_work_queue(
                work_queue.id, concurrency_limit=concurrency_limit
            )
            return
        except ObjectNotFound:
            pass
        await client.create_work_queue(
            work_queue_name,
            work_pool_name=work_pool_name,
            concurrency_limit=concurrency_limit,
        )


class FlowRegistry:
    flow_infos: list[FlowInfo]
    name: str

    def __init__(self, name: str) -> None:
        self.flow_infos = []
        self.name = name

    def flow(
        self,
        *,
        deployments: Union[DeploymentInfo, list[DeploymentInfo], None] = None,
        **kwargs,
    ):
        def decorated(fn):
            dep_list = deployments
            fn = datadog_event(fn)
            prefect_flow = flow(fn, **kwargs)
            if dep_list is None:
                dep_list = [DeploymentInfo(name=prefect_flow.name)]
            self.flow_infos.append(FlowInfo(flow=prefect_flow, deployments=dep_list))
            return prefect_flow

        return decorated

    async def create_flow_deployments(
        self,
        work_pool: str,
        base_job_manifest: KubernetesManifest,
        namespace: str,
        tags: Optional[list[str]] = None,
    ) -> None:
        if tags is None:
            tags = []
        flow_group_tags = [f"flowregistry:{self.name}"]

        deployment_tags = tags + flow_group_tags

        await create_work_pool_if_not_exists(work_pool)

        deployment_ids = set()
        for flow_info in self.flow_infos:
            for deploy_info in flow_info.deployments:
                await update_or_create_work_queue(
                    deploy_info.name,
                    work_pool,
                    deploy_info.concurrency_limit,
                )
            flow_deployments = await flow_info.get_deployments(
                work_pool,
                base_job_manifest,
                namespace,
                tags=deployment_tags,
            )
            for d in flow_deployments:
                r = await d.apply()
                deployment_ids.add(r)
                logger.info(f"Created deployment with ID {r}")
        async with get_client() as client:
            all_flow_deployments = await client.read_deployments(
                deployment_filter=DeploymentFilter(
                    tags=DeploymentFilterTags(all_=flow_group_tags),
                )
            )
            for deployment in all_flow_deployments:
                if deployment.id not in deployment_ids:
                    await client.delete_deployment(deployment.id)
                    logger.info(f"Deleting deployment with ID {deployment.id}")
