from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from prefect import get_client
from prefect.client.orion import OrionClient
from prefect.deployments import Deployment
from prefect.exceptions import ObjectNotFound
from prefect.flows import Flow, flow
from prefect.orion.schemas.filters import DeploymentFilter, DeploymentFilterTags
from prefect.orion.schemas.schedules import SCHEDULE_TYPES
from prefect.infrastructure.kubernetes import KubernetesJob

DEFAULT_WQ = "default"
JOB_TTL_SECONDS = 120


@dataclass
class DeploymentInfo:
    name: str
    schedule: SCHEDULE_TYPES = None
    parameters: dict[str, Any] = field(default_factory=dict)
    tags: Optional[list[str]] = None
    concurrency: Optional[int] = None

    @property
    def queue(self) -> str:
        return self.name

    @property
    def queue_concurrency(self) -> Optional[int]:
        return self.concurrency

    async def create_for_flow(
        self,
        client: OrionClient,
        flow: Flow,
        img: str,
        namespace: str,
        in_tags: Optional[list[str]] = None,
    ) -> UUID:
        if in_tags is None:
            in_tags = []
        tags = in_tags.copy()
        if self.tags is not None:
            tags.extend(self.tags)

        try:
            work_queue = await client.read_work_queue_by_name(self.queue)
        except ObjectNotFound:

            work_queue = await client.create_work_queue(name=self.queue)
        if self.queue_concurrency is not None:
            await client.update_work_queue(
                work_queue.id,
                concurrency_limit=self.queue_concurrency,
            )
        manifest = KubernetesJob.base_job_manifest()
        manifest["spec"]["ttlSecondsAfterFinished"] = JOB_TTL_SECONDS
        manifest["spec"]["backoffLimit"] = 1
        manifest["metadata"]["labels"]["deployment"] = self.name

        infrastructure = KubernetesJob(
            image=img,
            namespace=namespace,
            manifest=manifest,
        )

        tags.append(f"deployment:{self.name}")

        deployment = await Deployment.build_from_flow(
            flow=flow,
            name=self.name,
            work_queue_name=self.queue,
            infrastructure=infrastructure,
            tags=tags,
            schedule=self.schedule,
            parameters=self.parameters,
        )
        deployment_id = await deployment.apply()
        return deployment_id


@dataclass
class FlowInfo:
    flow: Flow
    deployments: list[DeploymentInfo]

    async def create_deployments(
        self,
        client: OrionClient,
        img: str,
        namespace: str,
        tags: Optional[list[str]] = None,
    ) -> list[UUID]:
        deployment_ids = []
        for deploy in self.deployments:
            deployment_id = await deploy.create_for_flow(
                client,
                flow=self.flow,
                img=img,
                namespace=namespace,
                in_tags=tags,
            )
            deployment_ids.append(deployment_id)
        return deployment_ids


class FlowGroup:
    flow_infos: list[FlowInfo]
    name: str

    def __init__(self, name: str):
        self.flow_infos = []
        self.name = name

    def get_work_queues(self) -> list[str]:
        queue_names = []
        for flow_info in self.flow_infos:
            queue_names.extend([d.queue for d in flow_info.deployments])
        return queue_names

    def flow(
        self,
        *,
        deployments: Optional[list[DeploymentInfo]] = None,
        **kwargs,
    ):
        def decorated(fn):
            dep_list = deployments
            prefect_flow = flow(fn, **kwargs)
            if dep_list is None:
                dep_list = [
                    DeploymentInfo(
                        name=prefect_flow.name,
                    )
                ]
            self.flow_infos.append(
                FlowInfo(
                    flow=prefect_flow,
                    deployments=dep_list,
                )
            )
            return prefect_flow

        return decorated

    async def deploy_flows(
        self, img: str, namespace: str, tags: Optional[list[str]] = None
    ) -> None:
        if tags is None:
            tags = []
        flow_group_tags = [f"flowgroup:{self.name}"]

        deployment_tags = tags + flow_group_tags

        deployment_ids = set()
        async with get_client() as client:
            for flow_info in self.flow_infos:
                deployment_ids.update(
                    set(
                        await flow_info.create_deployments(
                            client,
                            img,
                            namespace,
                            tags=deployment_tags.copy(),
                        )
                    )
                )
            all_flow_deployments = await client.read_deployments(
                deployment_filter=DeploymentFilter(
                    tags=DeploymentFilterTags(all_=flow_group_tags),
                )
            )
            for deployment in all_flow_deployments:
                if deployment.id not in deployment_ids:
                    await client.delete_deployment(deployment.id)
