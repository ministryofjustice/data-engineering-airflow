import pulumi_kubernetes as k8s
from pulumi.resource import ResourceOptions

from ..base import eks_config, region
from ..iam.roles import instanceRole
from .cluster import cluster
from .github_actions import clusterRoleBinding, serviceAccount

chart = k8s.helm.v3.Chart(
    release_name="kube2iam",
    config=k8s.helm.v3.ChartOpts(
        chart="kube2iam",
        fetch_opts=k8s.helm.v3.FetchOpts(repo="https://jtblin.github.io/kube2iam"),
        namespace="kube-system",
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
    ),
    opts=ResourceOptions(
        depends_on=[serviceAccount, clusterRoleBinding],
        provider=cluster.provider,
        parent=cluster,
    ),
)
