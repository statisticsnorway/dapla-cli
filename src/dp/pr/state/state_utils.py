"""Utils for getting and setting the state."""

import json
import subprocess
import sys
from typing import Final

import questionary
from google.cloud import storage  # type: ignore
from prompt_toolkit.formatted_text import FormattedText
from rich import print

from ..const import BATCH_PROJECT_ID, STATE_BUCKET_NAME_URI, State, StateObjectName

CANCEL: Final[str] = "Cancel"


class StateObjectHandler:
    """Handles operations around persisting the state."""

    def __init__(self, bucket_name: str, user_project: str) -> None:
        """Initializes the class."""
        self.bucket_name = bucket_name
        self.user_project = user_project
        self.client: storage.Client | None = None
        self.bucket: storage.Bucket | None = None
        self.current_state: State | None = None

    def get_client(self) -> storage.Client:
        """Return a GCS storage client."""
        if self.client is None:
            self.client = storage.Client()
        return self.client

    def get_bucket(self) -> storage.Bucket:
        """Return a bucket object."""
        if self.bucket is None:
            self.bucket = self.get_client().bucket(
                bucket_name=self.bucket_name, user_project=self.user_project
            )
        return self.bucket

    def get_user_state(self) -> State | None:
        """Prompt the user to select a run from those available and return that run as a state object."""
        state_object_name = self.user_select_run(show_other_users=True)
        if not state_object_name:
            return None

        return self.fetch_state(state_object_name=state_object_name)

    def fetch_state(self, state_object_name: str | None = None) -> State:
        """Fetch a state object and deserialize it."""
        if not state_object_name:
            state_object_name = self.user_select_run()

        blob = self.get_bucket().blob(state_object_name)
        json_data = json.loads(blob.download_as_string())
        self.current_state = State(**json_data)
        return self.current_state

    def set_state(self, state: State) -> None:
        """Serialize the state object and write it to a json file in persistent storage."""
        self.current_state = state
        blob = self.get_bucket().blob(f"{state.name}.json")
        blob.upload_from_string(state.model_dump_json())

    def list_blobs(self, show_other_users: bool) -> list[str]:
        """Fetch a list of blobs from a bucket."""
        blobs = self.get_bucket().list_blobs()
        sorted_blobs = sorted(blobs, key=lambda b: b.updated, reverse=True)
        batch_blobs = [
            f"{blob.name}, {blob.updated.replace(microsecond=0)}"
            for blob in sorted_blobs
        ]

        if not show_other_users:
            result = subprocess.run(
                [
                    "gcloud",
                    "config",
                    "list",
                    "account",
                    "--format",
                    "value(core.account)",
                ],
                stdout=subprocess.PIPE,
                check=True,
            )
            run_invoker = result.stdout.decode().strip().replace("@ssb.no", "")
            batch_blobs = [
                blob_data for blob_data in batch_blobs if run_invoker in blob_data
            ]

        return batch_blobs

    def user_select_run(self, show_other_users: bool = False) -> StateObjectName:
        """Prompt the user to select a run from a list of available options."""
        batch_blobs = self.list_blobs(show_other_users)

        if batch_blobs is None or len(batch_blobs) == 0:
            print(
                "No state-files were found. Please create a new state-file with 'dp batch ready'."
            )
            sys.exit(1)

        if len(batch_blobs) == 1:
            state_object = batch_blobs[0]
        else:
            state_object = questionary.select(
                "Which run do you want to perform this action on?",
                choices=[*batch_blobs, questionary.Separator(), questionary.Choice(FormattedText([("bold fg:ansired", CANCEL)]))],  # type: ignore
            ).ask()

        if state_object in [None, CANCEL]:
            return None

        state_object_name = state_object.split(",")[0]
        print(f"[blue] Using state file with name {state_object_name}")
        return str(state_object_name)


# Global singleton for handling state
state_object_handler = StateObjectHandler(STATE_BUCKET_NAME_URI, BATCH_PROJECT_ID)
