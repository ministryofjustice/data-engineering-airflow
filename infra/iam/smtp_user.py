import pulumi_aws as aws
import json

from ..base import base_name, tagger

# create an IAM user who can send emails via SES
smtp_user = aws.iam.User(f"{base_name}-smtp-user",
                         name=f"{base_name}-smtp-user",
                         tags=tagger.create_tags(f"{base_name}-execution-role"),
                         )

# create an access key, which will form the SMTP user/pass
access_key = aws.iam.AccessKey("access_key", user=smtp_user.name)

# allow the user to send emails
# note: we can reduce the scope here if we wanted
policy = aws.iam.Policy(
    "ses-policy",
    name=f"{base_name}-ses-policy",
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": ["ses:SendRawEmail"], "Effect": "Allow", "Resource": "*"}
            ],
        }
    ),
    tags=tagger.create_tags(f"{base_name}-ses-policy"),
)

# finally attach the policy to the user so it can send emails
aws.iam.UserPolicyAttachment(
    "smtp", user=smtp_user.name, policy_arn=policy.arn,
)
