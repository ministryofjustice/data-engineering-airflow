from pulumi.resource import ResourceOptions
from pulumi_aws.iam import (
    GetPolicyDocumentStatementArgs,
    GetPolicyDocumentStatementPrincipalArgs,
    Role,
    RoleInlinePolicyArgs,
    get_policy,
    get_policy_document,
)

from ..base import account_id, base_name, tagger

executionRole = Role(
    resource_name=f"{base_name}-execution-role",
    assume_role_policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                effect="Allow",
                actions=["sts:AssumeRole"],
                principals=[
                    GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=[
                            "airflow-env.amazonaws.com",
                            "airflow.amazonaws.com",
                        ],
                    )
                ],
            )
        ]
    ).json,
    description="Execution role for Airflow",
    name=f"{base_name}-execution-role",
    tags=tagger.create_tags(f"{base_name}-execution-role"),
)

instanceRole = Role(
    resource_name=f"{base_name}-node-instance-role",
    assume_role_policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                principals=[
                    GetPolicyDocumentStatementPrincipalArgs(
                        identifiers=["ec2.amazonaws.com"], type="Service"
                    )
                ],
                actions=["sts:AssumeRole"],
            )
        ]
    ).json,
    inline_policies=[
        RoleInlinePolicyArgs(
            name="assume-role",
            policy=get_policy_document(
                statements=[
                    GetPolicyDocumentStatementArgs(
                        actions=["sts:AssumeRole"],
                        resources=[f"arn:aws:iam::{account_id}:role/airflow*"],
                    )
                ]
            ).json,
        ),
        RoleInlinePolicyArgs(
            name="cluster-autoscaler",
            policy=get_policy_document(
                statements=[
                    GetPolicyDocumentStatementArgs(
                        actions=[
                            "autoscaling:DescribeAutoScalingGroups",
                            "autoscaling:DescribeAutoScalingInstances",
                            "autoscaling:DescribeLaunchConfigurations",
                            "autoscaling:DescribeTags",
                            "autoscaling:SetDesiredCapacity",
                            "autoscaling:TerminateInstanceInAutoScalingGroup",
                        ],
                        resources=["*"],
                    )
                ]
            ).json,
        ),
    ],
    managed_policy_arns=[
        get_policy(arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy").arn,
        get_policy(
            arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
        ).arn,
        get_policy(arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy").arn,
    ],
    name=f"{base_name}-node-instance-role",
    tags=tagger.create_tags(f"{base_name}-node-instance-role"),
    opts=ResourceOptions(
        protect=True
    ),  # Protected as deletion will break assume role policies that reference this role
)
