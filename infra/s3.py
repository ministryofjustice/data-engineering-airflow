import json

from data_engineering_pulumi_components.aws import Bucket
from pulumi import ResourceOptions
from pulumi_aws.s3 import BucketObject

from .base import base_name, mwaa_config, tagger
from .eks.cluster import cluster

bucket = Bucket(name=f"mojap-{base_name}", tagger=tagger, versioning={"enabled": True})

requirementsBucketObject = BucketObject(
    resource_name=f"{base_name}-requirements",
    opts=ResourceOptions(parent=bucket),
    bucket=bucket.id,
    content=mwaa_config["requirements"],
    key="requirements.txt",
    server_side_encryption="AES256",
)


def prepare_kube_config(kube_config: str) -> str:
    kube_config["users"][0]["user"]["exec"]["args"] = kube_config["users"][0]["user"][
        "exec"
    ]["args"][:-2]
    return json.dumps(kube_config, indent=4)


BucketObject(
    resource_name=f"{base_name}-kube-config",
    opts=ResourceOptions(parent=bucket, depends_on=[cluster]),
    bucket=bucket.id,
    content=cluster.kubeconfig.apply(prepare_kube_config),
    key="dags/.kube/config",
    server_side_encryption="AES256",
)
