import asyncio
import time
from datetime import timedelta

from prefect import get_client, get_run_logger, task
from prefect.server.schemas.schedules import IntervalSchedule
from prefect.server.schemas.states import StateType
from prefect_utils.registry import DeploymentInfo, FlowRegistry

demo_flow_group = FlowRegistry("demo")


@demo_flow_group.flow(
    deployments=[
        DeploymentInfo(
            name="hello-all",
            schedule=IntervalSchedule(interval=timedelta(hours=1)),
            parameters={"name": "all"},
        ),
        DeploymentInfo(
            name="hello-nope",
            schedule=IntervalSchedule(interval=timedelta(hours=6)),
            parameters={"name": "nope"},
        ),
    ]
)
def demo_flow(name: str):
    logger = get_run_logger()
    logger.info(f"Hello {name}")


CHILD_DEPLOYMENT = DeploymentInfo(
    name="child-flow",
    concurrency=2,
)


@demo_flow_group.flow(
    deployments=[
        CHILD_DEPLOYMENT,
    ]
)
def child_flow(datum: int):
    logger = get_run_logger()
    logger.info(f"Child flow for datum {datum}")
    logger.info("Sleeping...")
    time.sleep(30)
    logger.info("I'm done now")


@task
async def trigger_child_flow(i: int):
    return await CHILD_DEPLOYMENT.run_deployment(
        child_flow,
        parameters={"datum": i},
    )


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
    for i in range(20):
        flow_runs.append(await trigger_child_flow(i))
    for run_id in flow_runs:
        await wait_for_flow_run(run_id)
