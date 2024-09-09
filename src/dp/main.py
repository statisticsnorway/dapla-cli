from typer import Typer

from . import lab

app = Typer()

app.add_typer(lab.app, name="lab")
