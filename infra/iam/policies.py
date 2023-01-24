from pulumi import ResourceOptions
from pulumi_aws.iam import GetPolicyDocumentStatementArgs, Policy, get_policy_document

from ..providers import dataProvider
from ..base import account_id, base_name, environment_name, region, tagger

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
        ]
    ).json,
    tags=tagger.create_tags(f"{base_name}-ui-access"),
    opts=ResourceOptions(provider=dataProvider)
)
