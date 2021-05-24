import pulumi_aws as aws
import pulumi_eks as eks
from pulumi import ResourceOptions

from ..base import base_name, caller_arn, eks_config, tagger
from ..iam.roles import executionRole, instanceRole
from ..vpc import private_subnets, vpc

cluster_config = eks_config["cluster"]

role_mappings = [
    eks.RoleMappingArgs(
        groups=["system:masters"],
        role_arn=executionRole.arn,
        username="mwaa-service",
    )
]
for role_arn in cluster_config["role_mappings"]["role_arns"]:
    role_mappings.append(
        eks.RoleMappingArgs(
            groups=["system:masters"],
            role_arn=role_arn,
            username=role_arn,
        )
    )


cluster = eks.Cluster(
    resource_name=base_name,
    create_oidc_provider=True,
    instance_role=instanceRole,
    name=base_name,
    private_subnet_ids=[private_subnet.id for private_subnet in private_subnets],
    provider_credential_opts=eks.KubeconfigOptionsArgs(role_arn=caller_arn),
    role_mappings=role_mappings,
    skip_default_node_group=True,
    version=str(cluster_config["kubernetes_version"]),
    vpc_id=vpc.id,
    tags=tagger.create_tags(name=base_name),
)

node_group_config = cluster_config["node_group"]

nodeGroup = aws.eks.NodeGroup(
    resource_name=base_name,
    ami_type=node_group_config.get("ami_type", "AL2_x86_64"),
    capacity_type=node_group_config.get("capacity_type", "SPOT"),
    cluster_name=cluster.name,
    disk_size=node_group_config.get("disk_size", 20),
    force_update_version=None,
    instance_types=node_group_config["instance_types"],
    node_group_name="airflow",
    node_role_arn=instanceRole.arn,
    release_version=node_group_config["ami_release_version"],
    scaling_config=aws.eks.NodeGroupScalingConfigArgs(
        **node_group_config["scaling_config"]
    ),
    subnet_ids=cluster.core.private_subnet_ids,
    tags=tagger.create_tags("airflow"),
    opts=ResourceOptions(parent=cluster),
)
