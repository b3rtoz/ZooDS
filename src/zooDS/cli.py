import typer
from .zooDS import zds


app = typer.Typer()
app.command()(zds)


if __name__ == "__main__":
    app()