import logging

from typer import Typer

from . import auth, lab

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Typer()
app.add_typer(auth.app, name="auth", help="Authenticate dp with Keycloak")
app.add_typer(lab.app, name="lab", help="Interact with Dapla Lab services")
