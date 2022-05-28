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
    enabled_cluster_log_types=[
        "api",
        "audit",
        "authenticator",
        "controllerManager",
        "scheduler",
    ],
    instance_role=instanceRole,
    name=base_name,
    private_subnet_ids=[private_subnet.id for private_subnet in private_subnets],
    provider_credential_opts=eks.KubeconfigOptionsArgs(role_arn=caller_arn),
    role_mappings=role_mappings,
    skip_default_node_group=True,
    version=str(cluster_config["kubernetes_version"]),
    vpc_cni_options=eks.VpcCniOptionsArgs(
        init_image=(
            f"602401143452.dkr.ecr.us-west-2.amazonaws.com/"
            f"amazon-k8s-cni-init:v{cluster_config['vpc_cni_version']}"
        ),
        image=(
            f"602401143452.dkr.ecr.us-west-2.amazonaws.com/"
            f"amazon-k8s-cni:v{cluster_config['vpc_cni_version']}"
        ),
    ),
    vpc_id=vpc.id,
    tags=tagger.create_tags(name=base_name),
)

node_groups = cluster_config["node_groups"]

for node_group in node_groups:
    if "taints" in node_group:
        taints = []
        for taint in node_group["taints"]:
            taints.append(
                aws.eks.NodeGroupTaintArgs(
                    effect=taint["effect"],
                    key=taint["key"],
                    value=taint.get("value", None),
                )
            )
    else:
        taints = None

    nodeGroup = aws.eks.NodeGroup(
        resource_name=f"{base_name}-{node_group['name']}",
        ami_type=node_group.get("ami_type", "AL2_x86_64"),
        capacity_type=node_group.get("capacity_type", "SPOT"),
        cluster_name=cluster.eks_cluster.name,
        disk_size=node_group.get("disk_size", 20),
        instance_types=node_group["instance_types"],
        labels=node_group.get("labels"),
        node_group_name=node_group["name"],
        node_role_arn=instanceRole.arn,
        release_version=node_group["ami_release_version"],
        scaling_config=aws.eks.NodeGroupScalingConfigArgs(
            **node_group["scaling_config"]
        ),
        subnet_ids=cluster.core.private_subnet_ids,
        taints=taints,
        tags=tagger.create_tags(f"{base_name}-{node_group['name']}"),
        opts=ResourceOptions(parent=cluster),
    )

    for i, (key, value) in enumerate(node_group.get("labels", {}).items()):
        aws.autoscaling.Tag(
            resource_name=f"{base_name}-{node_group['name']}-label-{i}",
            autoscaling_group_name=nodeGroup.resources.apply(
                lambda x: x[0]["autoscaling_groups"][0]["name"]
            ),
            tag=aws.autoscaling.TagTagArgs(
                key=f"k8s.io/cluster-autoscaler/node-template/label/{key}",
                value=value,
                propagate_at_launch=True,
            ),
            opts=ResourceOptions(parent=nodeGroup),
        )

    for i, taint in enumerate(node_group.get("taints", [])):
        aws.autoscaling.Tag(
            resource_name=f"{base_name}-{node_group['name']}-taint-{i}",
            autoscaling_group_name=nodeGroup.resources.apply(
                lambda x: x[0]["autoscaling_groups"][0]["name"]
            ),
            tag=aws.autoscaling.TagTagArgs(
                key=f"k8s.io/cluster-autoscaler/node-template/taint/{taint['key']}",
                value=(
                    f"{taint.get('value', '')}:"
                    f"{taint['effect'].title().replace('_', '')}"
                ),
                propagate_at_launch=True,
            ),
            opts=ResourceOptions(parent=nodeGroup),
        )
