from pulumi.resource import ResourceOptions
from pulumi_aws.iam import (
    AccessKey,
    GetPolicyDocumentStatementArgs,
    Policy,
    User,
    UserPolicyAttachment,
    get_policy_document,
)
from ..providers import dataProvider
from ..base import base_name, tagger

# create an IAM user who can send emails via SES
smtpUser = User(
    resource_name=f"{base_name}-smtp-user",
    name=f"{base_name}-smtp-user",
    tags=tagger.create_tags(f"{base_name}-execution-role"),
    opts=ResourceOptions(provider=dataProvider)
)

# create an access key, which will form the SMTP user/pass
accessKey = AccessKey(
    resource_name="access_key",
    user=smtpUser.name,
    opts=ResourceOptions(parent=smtpUser),
)

# allow the user to send emails
# note: we can reduce the scope here if we wanted
policy = Policy(
    resource_name=f"{base_name}-ses-policy",
    name=f"{base_name}-ses-policy",
    policy=get_policy_document(
        statements=[
            GetPolicyDocumentStatementArgs(
                actions=["ses:SendRawEmail"],
                effect="Allow",
                resources=["*"],
            )
        ]
    ).json,
    tags=tagger.create_tags(f"{base_name}-ses-policy"),
    opts=ResourceOptions(parent=smtpUser),
)

# finally attach the policy to the user so it can send emails
UserPolicyAttachment(
    resource_name="smtp",
    user=smtpUser.name,
    policy_arn=policy.arn,
    opts=ResourceOptions(parent=smtpUser),
)
