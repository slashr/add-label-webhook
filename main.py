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

custom_node_selector = environ.get("NODE_POOL")
if not custom_node_selector:
    webhook.error("The required environment variable 'NODE_POOL' isn't set. Exiting...")
    exit(1)


def patch(custom_selector: str, existing_selector: bool) -> base64:
    custom_selector_key, custom_selector_value = custom_selector.replace(" ", "").split(":")
    webhook.info(f"Got '{custom_selector}' as nodeSelector, patching...")

    if existing_selector:
        webhook.info(f"Found already existing node selector, replacing it.")
        patch_operations = [Patch(op="replace", value={f"{custom_selector_key}": f"{custom_selector_value}"}).dict()]
    else:
        patch_operations = [Patch(op="add", value={f"{custom_selector_key}": f"{custom_selector_value}"}).dict()]
    return base64.b64encode(json.dumps(patch_operations).encode())


def admission_review(uid: str, message: str, existing_selector: bool) -> dict:
    return {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": True,
            "patchType": "JSONPatch",
            "status": {"message": message},
            "patch": patch(custom_node_selector, existing_selector).decode(),
        },
    }


@app.post("/mutate")
def mutate_request(request: dict = Body(...)):
    uid = request["request"]["uid"]
    selector = request["request"]["object"]["spec"]["template"]["spec"]
    object_in = request["request"]["object"]

    webhook.info(f'Applying nodeSelector for {object_in["kind"]}/{object_in["metadata"]["name"]}.')

    return admission_review(
        uid,
        "Successfully added nodeSelector.",
        True if "nodeSelector" in selector else False,
    )
