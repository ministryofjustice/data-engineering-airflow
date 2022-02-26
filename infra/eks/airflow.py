import json

import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

from ..base import environment_name
from .cluster import cluster, cluster_provider
from .kube2iam import kube2iam

# See https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-eks-example.html

airflow_namespace = k8s.core.v1.Namespace(
    resource_name="airflow",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="airflow",
        annotations={
            "iam.amazonaws.com/allowed-roles": json.dumps(
                [f"airflow_{environment_name}*"]
            )
        },
    ),
    opts=ResourceOptions(
        provider=cluster_provider, depends_on=[kube2iam], parent=cluster
    ),
)

role = k8s.rbac.v1.Role(
    resource_name="airflow",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="mwaa-role", namespace=airflow_namespace.metadata.name
    ),
    rules=[
        k8s.rbac.v1.PolicyRuleArgs(
            api_groups=["", "apps", "batch", "extensions"],
            resources=[
                "jobs",
                "pods",
                "pods/attach",
                "pods/exec",
                "pods/log",
                "pods/portforward",
                "secrets",
                "services",
            ],
            verbs=["create", "describe", "delete", "get", "list", "patch", "update"],
        )
    ],
    opts=ResourceOptions(provider=cluster_provider, parent=cluster),
)

roleBinding = k8s.rbac.v1.RoleBinding(
    resource_name="airflow",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="mwaa-role-binding", namespace=airflow_namespace.metadata.name
    ),
    subjects=[k8s.rbac.v1.SubjectArgs(kind="User", name="mwaa-service")],
    role_ref=k8s.rbac.v1.RoleRefArgs(
        api_group="rbac.authorization.k8s.io", kind="Role", name="mwaa-role"
    ),
    opts=ResourceOptions(provider=cluster_provider, parent=cluster),
)
