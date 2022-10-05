from pulumi import ResourceOptions
from pulumi_aws.iam import (
    GetPolicyDocumentStatementArgs,
    GetPolicyDocumentStatementConditionArgs,
    GetPolicyDocumentStatementPrincipalArgs,
    Role,
    RoleInlinePolicyArgs,
    get_policy,
    get_policy_document,
)
from pulumi_aws.iam.role_policy import RolePolicy

from ..base import account_id, base_name, region, tagger

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
    managed_policy_arns=[
        get_policy(arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy").arn,
        get_policy(
            arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
        ).arn,
        get_policy(arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy").arn,
        get_policy(arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore").arn,
    ],
    name=f"{base_name}-node-instance-role",
    tags=tagger.create_tags(f"{base_name}-node-instance-role"),
    opts=ResourceOptions(
        protect=True
    ),  # Protected as deletion will break assume role policies that reference this role
)

clusterAutoscalerRole = Role(
    resource_name=f"{base_name}-cluster-autoscaler-role",
    assume_role_policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                principals=[
                    GetPolicyDocumentStatementPrincipalArgs(
                        identifiers=["ec2.amazonaws.com"], type="Service"
                    ),
                    GetPolicyDocumentStatementPrincipalArgs(
                        identifiers=[instanceRole.arn], type="AWS"
                    ),
                ],
                actions=["sts:AssumeRole"],
            ),
        ]
    ).json,
    inline_policies=[
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
                            "ec2:DescribeInstanceTypes",
                        ],
                        resources=["*"],
                    )
                ]
            ).json,
        ),
    ],
    name=f"{base_name}-cluster-autoscaler-role",
    tags=tagger.create_tags(f"{base_name}-cluster-autoscaler-role"),
)

RolePolicy(
    resource_name=f"{base_name}-node-instance-role-policy",
    name="assume-role",
    policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                actions=["sts:AssumeRole"],
                resources=[
                    f"arn:aws:iam::{account_id}:role/airflow*",
                    clusterAutoscalerRole.arn,
                ],
            )
        ]
    ).json,
    role=instanceRole.id,
    opts=ResourceOptions(parent=instanceRole),
)

defaultRole = Role(
    resource_name=f"{base_name}-default-pod-role",
    assume_role_policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                principals=[
                    GetPolicyDocumentStatementPrincipalArgs(
                        identifiers=["ec2.amazonaws.com"], type="Service"
                    )
                ],
                actions=["sts:AssumeRole"],
            ),
            GetPolicyDocumentStatementArgs(
                principals=[
                    GetPolicyDocumentStatementPrincipalArgs(
                        identifiers=[instanceRole.arn], type="AWS"
                    )
                ],
                actions=["sts:AssumeRole"],
            ),
        ]
    ).json,
    name=f"{base_name}-default-pod-role",
    tags=tagger.create_tags(f"{base_name}-default-pod-role"),
)

flowLogRole = Role(
    resource_name=f"{base_name}-flow-log-role",
    assume_role_policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                principals=[
                    GetPolicyDocumentStatementPrincipalArgs(
                        identifiers=["vpc-flow-logs.amazonaws.com"], type="Service"
                    )
                ],
                actions=["sts:AssumeRole"],
                conditions=[
                    GetPolicyDocumentStatementConditionArgs(
                        test="StringEquals",
                        values=[account_id],
                        variable="aws:SourceAccount",
                    ),
                    GetPolicyDocumentStatementConditionArgs(
                        test="ArnLike",
                        values=[f"arn:aws:ec2:{region}:{account_id}:vpc-flow-log/*"],
                        variable="aws:SourceArn",
                    ),
                ],
            )
        ]
    ).json,
    inline_policies=[
        RoleInlinePolicyArgs(
            name="cloudwatch-logs",
            policy=get_policy_document(
                statements=[
                    GetPolicyDocumentStatementArgs(
                        actions=[
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents",
                            "logs:DescribeLogGroups",
                            "logs:DescribeLogStreams",
                        ],
                        resources=["*"],
                    )
                ]
            ).json,
        )
    ],
    name=f"{base_name}-flow-log-role",
    tags=tagger.create_tags(f"{base_name}-flow-log-role"),
)
