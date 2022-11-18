from pathlib import Path

import pulumi_kubernetes as k8s
from pulumi import Alias, ResourceOptions

from ..base import eks_config
from .cluster import cluster, cluster_provider

# See https://github.com/open-policy-agent/gatekeeper-library/

kyverno_namespace = k8s.core.v1.Namespace(
    resource_name="kyverno-system",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="kyverno",
    ),
    opts=ResourceOptions(
        provider=cluster_provider, delete_before_replace=True, parent=cluster
    ),
)

# Deploys Keyverno based on the chart specified in the stack .yaml
kyverno = k8s.helm.v3.Release(
    resource_name="kyverno",
    chart="kyverno",
    create_namespace=True,
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://kyverno.github.io/kyverno/"
    ),
    name="kyverno",
    namespace=kyverno_namespace.metadata.name,
    skip_await=False,
    version=eks_config["kyverno"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster_provider,
        delete_before_replace=True,
        parent=kyverno_namespace,
        aliases=[Alias(parent=cluster)],
    ),
)

# Generic path to append specific policy locations to
policy_path = str(Path(__file__).parent) + "/policies/"

kyverno_privilege = k8s.yaml.ConfigFile(
    "kyverno-privilege-escalation",
    policy_path + "kyv.privilege_escalation.yaml",
    opts=ResourceOptions(
        provider=cluster_provider,
        delete_before_replace=True,
        parent=kyverno,
    ),
)

kyverno_non_root = k8s.yaml.ConfigFile(
    "kyverno-non-root",
    policy_path + "kyv.run_as_non_root.yaml",
    opts=ResourceOptions(
        provider=cluster_provider,
        delete_before_replace=True,
        parent=kyverno,
    ),
)

kyverno_non_root_user = k8s.yaml.ConfigFile(
    "kyverno-non-root-user",
    policy_path + "kyv.run_as_non_root_user.yaml",
    opts=ResourceOptions(
        provider=cluster_provider,
        delete_before_replace=True,
        parent=kyverno,
    ),
)
