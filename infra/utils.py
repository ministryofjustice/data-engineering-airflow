import json


def prepare_kube_config(kube_config: dict) -> str:
    kube_config["users"][0]["user"]["exec"]["args"] = kube_config["users"][0]["user"][
        "exec"
    ]["args"][:-2]
    return json.dumps(kube_config, indent=4)
