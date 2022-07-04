# Data Engineering Airflow

This repository defines all the infrastructure required to create:

- an Airflow environment (using
  [Amazon Managed Workflows for Apache Airflow (MWAA)](https://aws.amazon.com/managed-workflows-for-apache-airflow/))
- an EKS cluster on which tasks can be run using the `KubernetesPodOperator`

## Prerequisites

To work with this repository, you must have the following installed:

- [Python 3.9 or later](https://www.python.org/downloads/)
- [Pulumi](https://www.pulumi.com/docs/get-started/install/)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [Kubectl](https://kubernetes.io/docs/tasks/tools/#install-kubectl)
- [Node.js](https://nodejs.org/en/download/)

You should also:

1. Create a virtual environment:

   ```zsh
   python -m venv venv
   ```

2. Activate the environment:

   ```zsh
   source venv/bin/activate
   ```

3. Install dependencies:

   ```zsh
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Structure

All infrastructure is defined in the `infra` directory:

- `base.py` defines config objects and global resources
- `mwaa.py` defines the Airflow environment
- `outputs.py` defines Pulumi outputs
- `s3.py` defines S3 infrastructure, including the
  [bucket for MWAA](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-s3-bucket.html)
  and a `requirements.txt` file used to install
  [Python dependencies](https://docs.aws.amazon.com/mwaa/latest/userguide/working-dags-dependencies.html)
  within the Airflow environment
- `utils.py` contains utility functions
- `vpc.py` defines the
  [network infrastructure](https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html)
  required to create an MWAA environment

The `eks` directory contains all infrastructure related to EKS and Kubernetes:

- `cluster.py` defines the cluster itself and a managed node group
- `cluster_autoscaler.py` defines the Cluster Autoscaler Helm chart
- `gatekeeper.py` defines the Gatekeeper Helm chart and associated policies, the
  rego code for which are stored in the in the `policies` directory
- `kube2iam.py` defines the kube2iam Helm chart
- `airflow.py` defines a namespace on the cluster in which Airflow can run pods

The `iam` directory contains all infrastructure related to IAM:

- `policies.py` defines a policy to allow access to the Airflow UI
- `roles.py` defines the execution role for Airflow and the instance role used
  by nodes in the managed node group
- `role_policies.py` defines the role policy for the execution role for Airflow

## Node Groups

Each stack creates two node groups:

- standard
- high-memory

### Standard

Nodes in the standard node group are unlabeled and do not have any taints. They
should be used by all workloads, except those that are memory intensive. Pods
will be scheduled on standard nodes unless:

- they have tolerations that match the taints of another node group
- they have a node selector that matches the labels of another node group

### High-Memory

Nodes in the high-memory node group run on memory-optimised EC2 instances. This
node group should only be used for workloads that are memory intensive.

For a pod to be scheduled on a node in the high-memory node group, it must have
the following tolerations:

```yaml
tolerations:
  - key: "high-memory"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

It must also have the following node affinity:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: "high-memory"
              operator: "In"
              values:
                - "true"
```

## Tasks

### How to manually deploy or update an environment

To deploy or update an environment:

1.  Create an AWS Vault session with the `restricted-admin@data-engineering`
    role:

    ```zsh
    aws-vault exec -d 12h restricted-admin@data-engineering
    ```

2.  Select the relevant stack, for example, `dev`:

    ```zsh
    pulumi stack select dev
    ```

3.  Update the stack:

    ```zsh
    pulumi up --refresh
    ```

    If you get an error message during the update, try to run the update again
    before debugging.

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

### How to upgrade the VPC CNI version

For all available VPC CNI versions see the [GitHub releases](https://github.com/aws/amazon-vpc-cni-k8s/releases).

To upgrade the VPC CNI version, change the value of the
`eks.cluster.vpc_cni_version` field in the relevant Pulumi stack config.

### How to run tests

To run tests manually, run:

```zsh
python -m pytest tests/
```

### How to attach Airflow UI access policy to user roles

The Airflow UI access policy is automatically attached to all new users of the
Analytical Platform via the Control Panel, so you should not normally need to
run this script.

To manually attach the policy to all users, assume the restricted admin role in
the data account and run:

```zsh
python scripts/attach_role_policies.py
```

## Email Notifications

We use AWS Simple Email Service (SES) for email notifications.

We use `dataengineering@digital.justice.gov.uk` as the "from" email address. This email address has been added as a verified identity to the data account without assigning a default configuration set:
https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#verify-email-addresses-procedure

## Notes

Tags set on a managed node group are not automatically propagated to the
provisioned autoscaling group and consquently are not applied to EC2 instances
created by the autoscaling group.

To work around this, tags must be added to the autoscaling group provisioned by
the managed node group independently of the creation of the managed node group
itself.

This could lead to a situation where untagged EC2 instances are created between
the time at which the managed node group (and autoscaling group) are created and
the tags are added to the autoscaling group.

When creating a stack from new, you might need to run `pulumi` up multiple times
because Pulumi is unable to detect that resources were successfully created.
Simply ignore the error message and try to `pulumi up` again. You might also
need to refresh the pulumi stack. Only debug if the pulumi up fails again with
the same error message. Hence it is better to pulumi up locally first, and use
the `pulumi up` GitHub Action as a confirmation that the change has been
completed.

When creating a stack from new, the Transit Gateway (TGW) attachment status will
show as "Pending Acceptance" and Pulumi will fail to create the routes to the
TGW. You will need to request the DSO team to accept the TGW attachment. Once
the state changes to "Available", you can run `pulumi up` again to create the
routes to the TGW.

## Reference

- [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)
- [Gatekeeper](https://github.com/open-policy-agent/gatekeeper)
- [kube2iam](https://github.com/jtblin/kube2iam)

## Licence

[MIT Licence](LICENCE.md)
