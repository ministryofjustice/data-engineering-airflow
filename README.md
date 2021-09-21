# Data Engineering Airflow

This repository defines all the infrastructure required to create:

- an Airflow environment (using
  [Amazon Managed Workflows for Apache Airflow (MWAA)](https://aws.amazon.com/managed-workflows-for-apache-airflow/))
- an EKS cluster on which tasks can be run using the `KubernetesPodOperator`

## Prerequisites

To work with this repository, you must have the following installed:

- [Python 3.9 or later](https://www.python.org/downloads/)
- [Pulumi](https://www.pulumi.com/docs/get-started/install/)

You should also:

1.  Create a virtual environment:

        python -m venv venv

2.  Activate the environment:

        source venv/bin/activate

3.  Install dependencies:

        pip install -r requirements.txt

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
- `vpc.py` defines the
  [network infrastructure](https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html)
  required to create an MWAA environment

The `eks` directory contains all infrastructure related to EKS and Kubernetes:

- `cluster.py` defines the cluster itself and a managed node group
- `cluster_autoscaler.py` defines the cluster autoscaler Helm chart
- `kube2iam.py` defines the kube2iam Helm chart
- `namespaces/airflow.py` defines a namespace on the cluster in which Airflow
  can run pods

The `iam` directory contains all infrastructure related to IAM:

- `roles.py` defines the execution role for Airflow and the instance role used
  by nodes in the managed node group
- `role_policies.py` defines the role policy for the execution role for Airflow

## Tasks

### How to manually deploy or update an environment

To deploy or update an environment:

1.  Create an AWS Vault session with the `restricted-admin@data-engineering`
    role:

         aws-vault exec -d 12h restricted-admin@data-engineering

2.  Select the relevant stack, for example, `dev`:

        pulumi stack select dev

3.  Update the stack:

        pulumi up --refresh

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

###

## Licence

[MIT Licence](LICENCE.md)
