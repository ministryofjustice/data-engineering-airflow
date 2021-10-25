import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

from ..base import eks_config, region
from .cluster import cluster

release = k8s.helm.v3.Release(
    resource_name="cluster-autoscaler",
    chart="cluster-autoscaler",
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://kubernetes.github.io/autoscaler"
    ),
    name="cluster-autoscaler",
    namespace="default",
    skip_await=True,
    values={
        "autoDiscovery": {"clusterName": cluster.eks_cluster.name},
        "awsRegion": region,
        "fullnameOverride": "cluster-autoscaler",
    },
    version=eks_config["cluster_autoscaler"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster.provider,
        parent=cluster,
    ),
)
