import pulumi_kubernetes as k8s
from pulumi.resource import ResourceOptions

from ..base import eks_config, region
from ..iam.roles import defaultRole, instanceRole
from .cluster import cluster

kube2iam_namespace = k8s.core.v1.Namespace(
    resource_name="kube2iam-system",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="kube2iam-system",
        annotations={"iam.amazonaws.com/allowed-roles": '["*"]'},
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)

kube2iam = k8s.helm.v3.Release(
    resource_name="kube2iam",
    chart="kube2iam",
    create_namespace=True,
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://jtblin.github.io/kube2iam"
    ),
    name="kube2iam",
    namespace=kube2iam_namespace.metadata.name,
    skip_await=False,
    values={
        "aws": {"region": region},
        "rbac": {"create": True},
        "extraArgs": {
            "base-role-arn": instanceRole.arn.apply(
                lambda arn: arn.split("/")[0] + "/"
            ),
            "default-role": defaultRole.name,
            "namespace-restrictions": True,
        },
        "host": {"iptables": True, "interface": "eni+"},
        "tolerations": [{"operator": "Exists"}],
    },
    version=eks_config["kube2iam"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster.provider,
        parent=cluster,
    ),
)
