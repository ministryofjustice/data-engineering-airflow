from pulumi.resource import ResourceOptions
import pulumi_kubernetes as k8s
from .cluster import cluster
from ..base import region
from ..iam.roles import instanceRole


chart = k8s.helm.v3.Chart(
    release_name="kube2iam",
    config=k8s.helm.v3.ChartOpts(
        chart="kube2iam",
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
        fetch_opts=k8s.helm.v3.FetchOpts(repo="https://jtblin.github.io/kube2iam"),
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)
