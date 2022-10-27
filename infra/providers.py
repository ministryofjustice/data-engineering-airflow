import os

from pulumi_aws import Provider, ProviderAssumeRoleArgs, get_region

current = get_region()

# for GA: DataEngineeringGitHubAction
# for local: restricted-admin
infra_creator_role_name = os.getenv("INFRA_CREATOR_ROLE_NAME")

data_arn = f"arn:aws:iam::593291632749:role/{infra_creator_role_name}"
data_engineering_arn = f"arn:aws:iam::189157455002:role/{infra_creator_role_name}"

data_account_id = "593291632749"
data_engineering_id = "189157455002"

dataProvider = Provider(
    resource_name="data",
    assume_role=ProviderAssumeRoleArgs(role_arn=data_arn),
    region=current.name,
)

dataEngineeringProvider = Provider(
    resource_name="data-engineering",
    assume_role=ProviderAssumeRoleArgs(role_arn=data_engineering_arn),
    region=current.name,
)
