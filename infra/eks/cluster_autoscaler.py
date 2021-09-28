import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

from ..base import eks_config, region
from .cluster import cluster
from .namespaces.github_actions import clusterRoleBinding, namespace, serviceAccount

clusterAutoscaler = k8s.helm.v3.Chart(
    release_name="cluster-autoscaler",
    config=k8s.helm.v3.ChartOpts(
        chart="cluster-autoscaler",
        fetch_opts=k8s.helm.v3.FetchOpts(
            repo="https://kubernetes.github.io/autoscaler"
        ),
        namespace="kube-system",
        values={
            "autoDiscovery": {"clusterName": cluster.name},
            "awsRegion": region,
        },
        version=eks_config["cluster_autoscaler"]["chart_version"],
    ),
    opts=ResourceOptions(
        depends_on=[clusterRoleBinding, namespace, serviceAccount],
        provider=cluster.provider,
        parent=cluster,
    ),
)
