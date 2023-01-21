import asyncio
import time
from datetime import timedelta

from prefect import get_client, get_run_logger, task
from prefect.deployments import run_deployment
from prefect.orion.schemas.schedules import IntervalSchedule
from prefect.orion.schemas.states import StateType

from prefect_flows.utils.flow_group import DeploymentInfo, FlowGroup

demo_flow_group = FlowGroup("demo")


@demo_flow_group.flow(
    deployments=[
        DeploymentInfo(
            name="hello-all",
            schedule=IntervalSchedule(interval=timedelta(hours=1)),
            parameters={"name": "all"},
        ),
        DeploymentInfo(
            name="hello-nobody",
            schedule=IntervalSchedule(interval=timedelta(hours=6)),
            parameters={"name": "nobody"},
        ),
    ]
)
def demo_flow(name: str):
    logger = get_run_logger()
    logger.info(f"Hello {name}")


CHILD_DEPLOYMENT_NAME = "child-flow"


@demo_flow_group.flow(
    deployments=[
        DeploymentInfo(
            name=CHILD_DEPLOYMENT_NAME,
            concurrency=2,
        ),
    ]
)
def child_flow():
    logger = get_run_logger()
    logger.info("Sleeping...")
    time.sleep(30)
    logger.info("Im done now")


@task
async def trigger_child_flow():
    deployment_name = "%s/%s" % (
        child_flow.__name__.replace("_", "-"),
        CHILD_DEPLOYMENT_NAME,
    )
    flow_run = await run_deployment(name=deployment_name, timeout=0)
    return flow_run.id


@task
async def wait_for_flow_run(flow_run_id):
    logger = get_run_logger()
    async with get_client() as client:
        while True:
            flow_run = await client.read_flow_run(flow_run_id=flow_run_id)
            if flow_run.state.type in [
                StateType.COMPLETED,
                StateType.CANCELLED,
                StateType.CRASHED,
                StateType.FAILED,
            ]:
                logger.info(
                    f"Flow run {flow_run_id} finished with state {flow_run.state_name}"
                )
                return
            logger.info(f"Flow {flow_run_id} in state {flow_run.state_name}")
            await asyncio.sleep(5)


@demo_flow_group.flow(
    deployments=[
        DeploymentInfo(
            name="parent-flow",
            schedule=IntervalSchedule(interval=timedelta(minutes=5)),
            concurrency=1,
        ),
    ]
)
async def parent_flow():
    flow_runs = []
    for _ in range(20):
        flow_runs.append(await trigger_child_flow())
    for run_id in flow_runs:
        await wait_for_flow_run(run_id)
