from pulumi_aws.iam import (
    User,
    AccessKey,
    Policy,
    UserPolicyAttachment,
    get_policy_document,
    GetPolicyDocumentStatementArgs,
)
from pulumi.resource import ResourceOptions

from ..base import base_name, tagger

# create an IAM user who can send emails via SES
smtp_user = User(
    resource_name=f"{base_name}-smtp-user",
    name=f"{base_name}-smtp-user",
    tags=tagger.create_tags(f"{base_name}-execution-role"),
)

# create an access key, which will form the SMTP user/pass
access_key = AccessKey(
    resource_name="access_key",
    user=smtp_user.name,
    opts=ResourceOptions(parent=smtp_user),
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
    opts=ResourceOptions(parent=smtp_user),
)

# finally attach the policy to the user so it can send emails
UserPolicyAttachment(
    resource_name="smtp",
    user=smtp_user.name,
    policy_arn=policy.arn,
    opts=ResourceOptions(parent=smtp_user),
)
