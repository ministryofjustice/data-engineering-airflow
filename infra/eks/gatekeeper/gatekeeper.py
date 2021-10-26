import pulumi_kubernetes as k8s
from pulumi.resource import ResourceOptions
from pathlib import Path

from ...base import eks_config
from ..cluster import cluster

release = k8s.helm.v3.Release(
    resource_name="gatekeeper",
    chart="gatekeeper",
    repository_opts=k8s.helm.v3.RepositoryOptsArgs(
        repo="https://open-policy-agent.github.io/gatekeeper/charts"
    ),
    name="gatekeeper",
    namespace="default",
    skip_await=False,
    values={},
    version=eks_config["gatekeeper"]["chart_version"],
    opts=ResourceOptions(
        provider=cluster.provider,
        parent=cluster,
    ),
)

# Prevent privileged containers
with open(file=Path(__file__).parent / "policies/privileged.rego") as file:
    rego = file.read()

k8s.apiextensions.CustomResource(
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
                "rego": rego,
            }
        ],
    },
    opts=ResourceOptions(provider=cluster.provider, parent=release),
)

k8s.apiextensions.CustomResource(
    resource_name="privileged-constraint",
    api_version="constraints.gatekeeper.sh/v1beta1",
    kind="K8sPSPPrivilegedContainer",
    metadata=k8s.meta.v1.ObjectMetaArgs(name="psp-privileged-container"),
    spec={
        "match": {
            "kinds": [{"apiGroups": [""], "kinds": ["Pod"]}],
            "excludedNamespaces": ["kube-system"],
        }
    },
    opts=ResourceOptions(provider=cluster.provider, parent=release),
)

# Prevent privilege escalation
with open(
    file=Path(__file__).parent / "policies/allow_privilege_escalation.rego"
) as file:
    rego = file.read()

k8s.apiextensions.CustomResource(
    resource_name="allow-privilege-escalation-template",
    api_version="templates.gatekeeper.sh/v1beta1",
    kind="Template",
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
                "rego": rego,
            }
        ],
    },
    opts=ResourceOptions(provider=cluster.provider, parent=release),
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
            "excludedNamespaces": ["kube-system"],
        }
    },
    opts=ResourceOptions(provider=cluster.provider, parent=release),
)
