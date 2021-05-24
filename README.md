# Data Engineering Airflow

### How to upgrade the Kubernetes version

For all available Kubernetes versions, see the
[Amazon EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html).

To upgrade the Kubernetes version, change the value of the
`eks.cluster.kubernetes_version` field in the relevant Pulumi stack config.

When upgrading the Kubernetes version you should also
[upgrade the node group AMI release version](#how-to-upgrade-the-node-group-ami-release-version).

### How to upgrade the node group AMI release version

For all available AMI release versions, see the
[Amazon EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/eks-linux-ami-versions.html).

To upgrade the AMI release version, change the value of the
`eks.cluster.node_group.ami_release_version` field in the relevant Pulumi stack
config.

The AMI release version should match the Kubernetes version. For example, if the
Kubernetes version is `1.20`, you should specify an AMI release version with the
tag `1.20.*-*`.

## Licence

[MIT Licence](LICENCE.md)
