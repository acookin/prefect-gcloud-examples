import asyncio
import logging
from importlib import import_module
from typing import Optional

import click

from prefect_utils.deploy.manifest import get_base_manifest
from prefect_utils.registry import FlowRegistry

logger = logging.getLogger(__name__)


def get_flow_registry(module_instance: str) -> FlowRegistry:
    try:
        module_name, instance_name = tuple(module_instance.split(":"))
    except ValueError:
        raise ValueError(f"{module_instance} is not a valid argument")

    module = import_module(module_name)
    instance = getattr(module, instance_name)
    if not isinstance(instance, FlowRegistry):
        raise ValueError(
            f"{module_instance} is of type {type(instance)} and must be FlowRegistry"
        )

    return instance


@click.group()
@click.option("--debug/--no-debug")
def cli(debug):
    log_level = "DEBUG" if debug else "INFO"
    logger.setLevel(log_level)


@cli.command()
@click.option(
    "--flow-registry",
    help="Python module in the format MODULE:INSTANCE",
    required=True,
)
@click.option("--pool", help="work pool name", required=True)
@click.option("--namespace", help="reference to k8s namespace", required=True)
@click.option(
    "--image",
    help="Image to deploy",
    required=True,
)
@click.option(
    "--config-map",
    help="config map reference",
    required=True,
)
@click.option(
    "--env",
    help="environment label",
    required=True,
)
@click.option(
    "--app",
    help="app name",
    required=True,
)
@click.option(
    "--service-account",
    help="k8s service account",
)
def deploy(
    flow_registry: str,
    pool: str,
    namespace: str,
    image: str,
    config_map: str,
    env: str,
    app: str,
    service_account: str,
):
    registry = get_flow_registry(flow_registry)
    base_manifest = get_base_manifest(
        image,
        config_map,
        namespace,
        env,
        app,
        service_account,
    )
    asyncio.run(registry.create_flow_deployments(pool, base_manifest, namespace))


def run():
    cli(auto_envvar_prefix="PRFCT")


if __name__ == "__main__":
    run()
