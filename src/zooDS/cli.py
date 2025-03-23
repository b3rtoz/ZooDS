import typer
from .user_interface import zds


app = typer.Typer()
app.command()(zds)


if __name__ == "__main__":
    app()