import pulumi_aws as aws
import pulumi_eks as eks
import pulumi_kubernetes as k8s
from pulumi import Output, ResourceOptions
from ..cluster import cluster
from ..kube2iam import chart
from ...iam.roles import instanceRole
from ...base import tagger

# See https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-eks-example.html

namespace = k8s.core.v1.Namespace(
    resource_name="airflow",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="airflow",
        annotations={"iam.amazonaws.com/allowed-roles": '["(dev|alpha)_.*"]'},
    ),
    opts=ResourceOptions(provider=cluster.provider, depends_on=[chart], parent=cluster),
)

role = k8s.rbac.v1.Role(
    resource_name="airflow",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="mwaa-role", namespace=namespace.metadata.name
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
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)

roleBinding = k8s.rbac.v1.RoleBinding(
    resource_name="airflow",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="mwaa-role-binding", namespace=namespace.metadata.name
    ),
    subjects=[k8s.rbac.v1.SubjectArgs(kind="User", name="mwaa-service")],
    role_ref=k8s.rbac.v1.RoleRefArgs(
        api_group="rbac.authorization.k8s.io", kind="Role", name="mwaa-role"
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)
