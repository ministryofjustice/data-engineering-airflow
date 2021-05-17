from pulumi import Output, ResourceOptions
from pulumi_aws.iam import (
    GetPolicyDocumentStatementArgs,
    GetPolicyDocumentStatementConditionArgs,
    RolePolicy,
    get_policy_document,
)

from ..base import account_id, base_name, environment_name, region
from ..eks.cluster import cluster
from ..s3 import bucket
from .roles import executionRole


def get_execution_role_policy(args):
    account_id = args["account_id"]
    bucket_arn = args["bucket_arn"]
    cluster_arn = args["cluster_arn"]
    environment_name = args["environment_name"]
    region = args["region"]

    return get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                actions=["airflow:PublishMetrics"],
                resources=[
                    f"arn:aws:airflow:{region}:{account_id}:environment/"
                    f"{environment_name}"
                ],
            ),
            GetPolicyDocumentStatementArgs(
                actions=["s3:ListAllMyBuckets"], effect="Deny", resources=["*"]
            ),
            GetPolicyDocumentStatementArgs(
                actions=["s3:GetObject*", "s3:GetBucket*", "s3:List*"],
                resources=[bucket_arn, f"{bucket_arn}/*"],
            ),
            GetPolicyDocumentStatementArgs(
                actions=[
                    "logs:CreateLogStream",
                    "logs:CreateLogGroup",
                    "logs:PutLogEvents",
                    "logs:GetLogEvents",
                    "logs:GetLogRecord",
                    "logs:GetLogGroupFields",
                    "logs:GetQueryResults",
                    "logs:DescribeLogGroups",
                ],
                resources=[
                    f"arn:aws:logs:{region}:{account_id}:log-group:"
                    f"airflow-{environment_name}-*"
                ],
            ),
            GetPolicyDocumentStatementArgs(
                actions=["cloudwatch:PutMetricData"], resources=["*"]
            ),
            GetPolicyDocumentStatementArgs(
                actions=[
                    "sqs:ChangeMessageVisibility",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                    "sqs:ReceiveMessage",
                    "sqs:SendMessage",
                ],
                resources=[f"arn:aws:sqs:{region}:*:airflow-celery-*"],
            ),
            GetPolicyDocumentStatementArgs(
                actions=[
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:GenerateDataKey*",
                    "kms:Encrypt",
                ],
                not_resources=[f"arn:aws:kms:*:{account_id}:key/*"],
                conditions=[
                    GetPolicyDocumentStatementConditionArgs(
                        test="StringLike",
                        variable="kms:ViaService",
                        values=[f"sqs.{region}.amazonaws.com"],
                    )
                ],
            ),
            GetPolicyDocumentStatementArgs(
                actions=["eks:DescribeCluster"], resources=[cluster_arn]
            ),
        ]
    ).json


executionRolePolicy = RolePolicy(
    resource_name=f"{base_name}-execution-role-policy",
    name=f"{base_name}-execution-role-policy",
    policy=Output.all(
        account_id=account_id,
        bucket_arn=bucket.arn,
        cluster_arn=cluster.core.cluster.arn,
        environment_name=environment_name,
        region=region,
    ).apply(get_execution_role_policy),
    role=executionRole.id,
    opts=ResourceOptions(parent=executionRole, depends_on=[bucket, cluster]),
)
