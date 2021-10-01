import pulumi_kubernetes as k8s
from pulumi.resource import ResourceOptions

from ..base import eks_config, region
from ..iam.roles import instanceRole
from .cluster import cluster

release = k8s.helm.v3.Release(
    resource_name="kube2iam",
    chart="kube2iam",
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://jtblin.github.io/kube2iam"
    ),
    name="kube2iam",
    namespace="default",
    skip_await=True,
    values={
        "aws": {"region": region},
        "rbac": {"create": True},
        "extraArgs": {
            "base-role-arn": instanceRole.arn.apply(
                lambda arn: arn.split("/")[0] + "/"
            ),
            "default-role": instanceRole.name,
            "namespace-restrictions": True,
            "namespace-restriction-format": "regexp",
        },
        "host": {"iptables": True, "interface": "eni+"},
    },
    version=eks_config["kube2iam"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster.provider,
        parent=cluster,
    ),
)
