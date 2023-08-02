from pulumi import InvokeOptions, ResourceOptions
from pulumi_aws.iam import GetPolicyDocumentStatementArgs, Policy, get_policy_document

from ..base import account_id, base_name, environment_name, region, tagger
from ..providers import data_provider

Policy(
    resource_name=base_name,
    name=f"{base_name}-ui-access",
    policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                actions=["airflow:CreateWebLoginToken"],
                resources=[
                    f"arn:aws:airflow:{region}:{account_id}:role/"
                    f"{environment_name}/User"
                ],
            )
        ],
        opts=InvokeOptions(provider=data_provider),
    ).json,
    tags=tagger.create_tags(f"{base_name}-ui-access"),
    opts=ResourceOptions(provider=data_provider),
)
