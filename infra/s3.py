import json

from data_engineering_pulumi_components.aws import Bucket
from pulumi import ResourceOptions
from pulumi_aws.s3 import BucketObject, BucketPolicy

from .base import base_name, mwaa_config, tagger
from .eks.cluster import cluster
from .providers import data_provider
from .utils import prepare_kube_config

bucket = Bucket(
    name=f"mojap-{base_name}",
    tagger=tagger,
    versioning={"enabled": True},
    opts=ResourceOptions(provider=data_provider),
)


statement = {
    "Sid": "AirflowBucketPolicy",
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::593291632749:role/data-ga-s3-sync"},
    "Action": [
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:ListBucketVersions",
    ],
    "Resource": [
        f"arn:aws:s3:::mojap-{base_name}",
        f"arn:aws:s3:::mojap-{base_name}/*",
    ],
}

policy = json.dumps({"Version": "2012-10-17", "Statement": statement})

bucket_policy = BucketPolicy(
    resource_name=f"mojap-{base_name}-bucket-policy",
    bucket=f"mojap-{base_name}",
    policy=policy,
    opts=ResourceOptions(parent=bucket, depends_on=bucket),
)

requirementsBucketObject = BucketObject(
    resource_name=f"{base_name}-requirements",
    opts=ResourceOptions(parent=bucket),
    bucket=bucket.id,
    content=mwaa_config["requirements"],
    key="requirements.txt",
    server_side_encryption="AES256",
)

BucketObject(
    resource_name=f"{base_name}-kube-config",
    opts=ResourceOptions(parent=bucket, depends_on=[cluster]),
    bucket=bucket.id,
    content=cluster.kubeconfig.apply(prepare_kube_config),
    key="dags/.kube/config",
    server_side_encryption="AES256",
)
