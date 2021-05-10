from .eks.cluster import cluster
from pulumi import export

export("kubeconfig", cluster.kubeconfig)
