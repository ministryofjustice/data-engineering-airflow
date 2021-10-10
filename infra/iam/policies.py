from pulumi_aws.iam import Policy, get_policy_document, GetPolicyDocumentStatementArgs
from ..base import base_name, tagger, environment_name, region, account_id

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
)
