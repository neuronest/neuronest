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
):
    """Deploy a model to Vertex AI."""
    if ctx.obj.verbose:
        typer.echo("Dummy echo")

    deploy_model_main()


app.add_typer(deploy_app, name="deploy")
