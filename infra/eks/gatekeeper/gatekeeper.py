from pathlib import Path

import pulumi_kubernetes as k8s
from pulumi.resource import ResourceOptions

from ...base import eks_config
from ..cluster import cluster
from ..kube2iam import kube2iam_namespace
from ..cluster_autoscaler import cluster_autoscaler_namespace

# See https://github.com/open-policy-agent/gatekeeper-library/

namespace = k8s.core.v1.Namespace(
    resource_name="gatekeeper-system",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="gatekeeper-system",
    ),
    opts=ResourceOptions(provider=cluster.provider, parent=cluster),
)

gatekeeper = k8s.helm.v3.Release(
    resource_name="gatekeeper",
    chart="gatekeeper",
    create_namespace=True,
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://open-policy-agent.github.io/gatekeeper/charts"
    ),
    name="gatekeeper",
    namespace=namespace.metadata.name,
    skip_await=False,
    version=eks_config["gatekeeper"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster.provider,
        parent=cluster,
    ),
)

excluded_namespaces = [
    "default",
    "kube-system",
    cluster_autoscaler_namespace.metadata.name,
    kube2iam_namespace.metadata.name,
]

# Prevent privileged containers
with open(file=Path(__file__).parent / "policies/privileged.rego") as file:
    privileged_rego = file.read()

privilegedTemplate = k8s.apiextensions.CustomResource(
    resource_name="privileged-template",
    api_version="templates.gatekeeper.sh/v1beta1",
    kind="ConstraintTemplate",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="k8spspprivilegedcontainer"),
    spec={
        "crd": {
            "spec": {
                "names": {"kind": "K8sPSPPrivilegedContainer"},
                "validation": {
                    "openAPIV3Schema": {
                        "description": (
                            "Controls the ability of any container to enable "
                            "privileged mode. Corresponds to the privileged field in a "
                            "PodSecurityPolicy."
                        )
                    }
                },
            }
        },
        "targets": [
            {
                "target": "admission.k8s.gatekeeper.sh",
                "rego": privileged_rego,
            }
        ],
    },
    opts=ResourceOptions(provider=cluster.provider, parent=gatekeeper),
)

k8s.apiextensions.CustomResource(
    resource_name="privileged-constraint",
    api_version="constraints.gatekeeper.sh/v1beta1",
    kind="K8sPSPPrivilegedContainer",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="psp-privileged-container"),
    spec={
        "match": {
            "kinds": [{"apiGroups": [""], "kinds": ["Pod"]}],
            "excludedNamespaces": excluded_namespaces,
        }
    },
    opts=ResourceOptions(provider=cluster.provider, parent=privilegedTemplate),
)

# Prevent privilege escalation
with open(
    file=Path(__file__).parent / "policies/allow_privilege_escalation.rego"
) as file:
    allow_privilege_escalation_rego = file.read()

allowPrivilegeEscalationTemplate = k8s.apiextensions.CustomResource(
    resource_name="allow-privilege-escalation-template",
    api_version="templates.gatekeeper.sh/v1beta1",
    kind="ConstraintTemplate",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="k8spspallowprivilegeescalationcontainer"),
    spec={
        "crd": {
            "spec": {
                "names": {"kind": "K8sPSPAllowPrivilegeEscalationContainer"},
                "validation": {
                    "openAPIV3Schema": {
                        "description": (
                            "Controls restricting escalation to root privileges. "
                            "Corresponds to the allowPrivilegeEscalation field in a "
                            "PodSecurityPolicy."
                        )
                    }
                },
            }
        },
        "targets": [
            {
                "target": "admission.k8s.gatekeeper.sh",
                "rego": allow_privilege_escalation_rego,
            }
        ],
    },
    opts=ResourceOptions(provider=cluster.provider, parent=gatekeeper),
)

k8s.apiextensions.CustomResource(
    resource_name="allow-privilege-escalation-constraint",
    api_version="constraints.gatekeeper.sh/v1beta1",
    kind="K8sPSPAllowPrivilegeEscalationContainer",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="psp-allow-privilege-escalation-container"
    ),
    spec={
        "match": {
            "kinds": [{"apiGroups": [""], "kinds": ["Pod"]}],
            "excludedNamespaces": excluded_namespaces,
        }
    },
    opts=ResourceOptions(
        provider=cluster.provider, parent=allowPrivilegeEscalationTemplate
    ),
)
