from pulumi import export

from .eks.cluster import cluster

export("kubeconfig", cluster.kubeconfig)
