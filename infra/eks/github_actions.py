import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

from .cluster import cluster

serviceAccount = k8s.core.v1.ServiceAccount(
    resource_name="github-actions-runner",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="github-actions-runner", namespace="kube-system"
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)

clusterRoleBinding = k8s.rbac.v1.ClusterRoleBinding(
    resource_name="github-actions-runner",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="github-actions-runner", namespace="kube-system"
    ),
    subjects=[
        k8s.rbac.v1.SubjectArgs(
            kind="ServiceAccount",
            name=serviceAccount.metadata.name,
            namespace=serviceAccount.metadata.namespace,
        )
    ],
    role_ref=k8s.rbac.v1.RoleRefArgs(
        api_group="rbac.authorization.k8s.io", kind="ClusterRole", name="cluster-admin"
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)
