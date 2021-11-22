import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

from ..base import eks_config, region
from .cluster import cluster
from ..iam.roles import clusterAutoscalerRole

cluster_autoscaler_namespace = k8s.core.v1.Namespace(
    resource_name="cluster-autoscaler-system",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="cluster-autoscaler-system",
        annotations={
            "iam.amazonaws.com/allowed-roles": clusterAutoscalerRole.name.apply(
                lambda name: f'["{name}"]'
            )
        },
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)

clusterAutoscaler = k8s.helm.v3.Release(
    resource_name="cluster-autoscaler",
    chart="cluster-autoscaler",
    create_namespace=True,
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://kubernetes.github.io/autoscaler"
    ),
    name="cluster-autoscaler",
    namespace=cluster_autoscaler_namespace.metadata.name,
    skip_await=False,
    values={
        "autoDiscovery": {"clusterName": cluster.eks_cluster.name},
        "awsRegion": region,
        "fullnameOverride": "cluster-autoscaler",
        "podAnnotations": {
            "cluster-autoscaler.kubernetes.io/safe-to-evict": "false",
            "iam.amazonaws.com/role": clusterAutoscalerRole.name,
        },
    },
    version=eks_config["cluster_autoscaler"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster.provider,
        parent=cluster,
    ),
)
