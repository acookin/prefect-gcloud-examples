import asyncio
import pathlib
import shutil

import click
from jinja2 import Environment, PackageLoader, select_autoescape

from prefect_flows.flows import FLOW_GROUPS

DEFAULT_NAMESPACE = "prefect"


@click.group()
def cli():
    pass


@cli.command()
@click.option("-i", "--image", "image")
def deploy_flows(image):
    for fg in FLOW_GROUPS:
        asyncio.run(fg.deploy_flows(image, DEFAULT_NAMESPACE))


@cli.command()
def gen_agent_manifests():
    click.echo("deploying agent")
    env = Environment(
        loader=PackageLoader("prefect_flows"), autoescape=select_autoescape()
    )
    overlay_directory = (
        pathlib.Path(__file__).parent.resolve().parent.resolve().parent.resolve()
        / "k8s"
        / "prefect-agent"
        / "overlays"
    )
    if not overlay_directory.exists():
        raise ValueError(f"{overlay_directory} does not exist")

    kustomize_tmpl = env.get_template("kustomize.yaml")
    patch_tmpl = env.get_template("patch.yaml")
    for fg in FLOW_GROUPS:
        fg_overlay_dir = overlay_directory / fg.name
        if fg_overlay_dir.exists():
            shutil.rmtree(fg_overlay_dir)
        fg_overlay_dir.mkdir()
        kustomize_file = fg_overlay_dir / "kustomization.yaml"
        patch_file = fg_overlay_dir / "deployment.yaml"
        kustomization = kustomize_tmpl.render(flow_group_name=fg.name)
        with kustomize_file.open("w") as f:
            f.write(kustomization)
        click.echo(f"Wrote kustomization for flow group {fg.name} to {kustomize_file}")
        patch = patch_tmpl.render(
            work_queues=fg.get_work_queues(), flow_group_name=fg.name
        )
        with patch_file.open("w") as f:
            f.write(patch)
        click.echo(f"Wrote patch for flow group {fg.name} to {patch_file}")


if __name__ == "__main__":
    cli()
