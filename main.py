from fastapi import FastAPI, Body
from os import environ
from models import Patch
import logging
import base64
import json

app = FastAPI()

webhook = logging.getLogger(__name__)
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.removeHandler(uvicorn_logger.handlers[0])  # Turn off uvicorn duplicate log
webhook.setLevel(logging.INFO)
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s")

custom_label = environ.get("NODE_POOL")
if not custom_label:
    webhook.error("The required environment variable 'NODE_POOL' isn't set. Exiting...")
    exit(1)


def patch(existing_labels: dict) -> base64:
    custom_label_key, custom_label_value = custom_label.replace(" ", "").split(":")
    webhook.info(f"Got '{custom_label}' as label, patching...")

    existing_label_values = existing_labels.values()
    patch_operations = []  # Initialize with an empty list

    for value in existing_label_values:
        if value == "promtail":
            webhook.info(f"Adding monitoring label")
            patch_operations = [Patch(op="add", value={f"{custom_label_key}": f"{custom_label_value}"}).dict()]
    return base64.b64encode(json.dumps(patch_operations).encode())


def admission_review(uid: str, message: str, existing_labels: dict) -> dict:
    return {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": True,
            "patchType": "JSONPatch",
            "status": {"message": message},
            "patch": patch(existing_labels).decode(),
        },
    }


@app.post("/mutate")
def mutate_request(request: dict = Body(...)):
    uid = request["request"]["uid"]
    labels = request["request"]["object"]["metadata"]["labels"]
    object_in = request["request"]["object"]

    webhook.info(f'Applying nodeSelector for {object_in["kind"]}/{object_in["metadata"]["name"]}.')

    return admission_review(
        uid,
        "Successfully added label.",
        labels,
    )
