"""Command-line entry point for the RootGuard defense layer."""

from importlib.metadata import PackageNotFoundError, version

import typer

app = typer.Typer(no_args_is_help=True)
dev_app = typer.Typer()
app.add_typer(dev_app, name="dev")


def _get_version() -> str:
    try:
        return version("rootguard")
    except PackageNotFoundError:
        return "0.0.0.dev0"


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"rootguard {_get_version()}")
        raise typer.Exit()


@app.callback()
def main(
    version_flag: bool = typer.Option(
        False, "--version", callback=version_callback, is_eager=True
    ),
) -> None:
    return
