from pulumi_aws import Provider, ProviderAssumeRoleArgs

data_provider = Provider(
    resource_name="data",
    assume_role=ProviderAssumeRoleArgs(
        role_arn="arn:aws:iam::593291632749:role/data-engineering-infrastructure"
    ),
    region="eu-west-1",
)
