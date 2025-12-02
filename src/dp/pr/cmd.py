"""Batch update commands.

Commands invoked by dpteam batch <some-command> are defined here.
"""

import warnings

import typer

from .approve.cmd import approve
from .atlantis_apply.cmd import apply
from .atlantis_plan.cmd import plan
from .merge.cmd import merge
from .probe.cmd import app as state
from .ready.cmd import ready
from .state.cmd import app as probe

app = typer.Typer(no_args_is_help=True)


# Remove gcloud warnings under development
warnings.filterwarnings(
    "ignore", message="Your application has authenticated using end user credentials from Google Cloud SDK without a quota project."
)


@app.callback()
def pr() -> None:
    """Do PR operations."""
    pass


app.command()(approve)
app.command()(open)
app.command()(merge)
app.command()(apply)
app.command()(plan)
app.command()(ready)
#app.add_typer(janitor.app)
app.add_typer(state)
app.add_typer(probe)
#app.add_typer(add)
