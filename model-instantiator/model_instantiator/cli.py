import typer
from pydantic import BaseModel

from model_instantiator.jobs.deploy_model import main as deploy_model_main

app = typer.Typer()
deploy_app = typer.Typer()


class CLIState(BaseModel):
    verbose: bool = False


@app.callback()
def main(
    context: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
):
    """Model Instantiator CLI"""
    context.obj = CLIState(verbose=verbose)
    if context.obj.verbose:
        typer.echo("Verbose mode enabled")


@deploy_app.command("model")
def deploy_model_cli(
    ctx: typer.Context,
    model_name: str = typer.Option(
        ..., "--model_name", help="Name of the model to deploy."
    ),
    cloud_scheduler_job_name: str = typer.Option(
        ..., "--cloud_scheduler_job_name", help="Cloud Scheduler job name."
    ),
):
    """Deploy a model to Vertex AI."""
    if ctx.obj.verbose:
        typer.echo(
            f"Deploying model '{model_name}' with job '{cloud_scheduler_job_name}'"
        )

    deploy_model_main(
        model_name=model_name,
        cloud_scheduler_job_name=cloud_scheduler_job_name,
    )


app.add_typer(deploy_app, name="deploy")
