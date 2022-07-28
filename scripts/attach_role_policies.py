# This script will attach the airflow-dev-ui-access and airflow-prod-ui-access policies
# to all alpha_user_* roles.
#
# This script should only need to be run once, as long as the policies are attached by
# default when a user logs in to the control panel for the first time.

import boto3

client = boto3.client("iam")
paginator = client.get_paginator("list_roles")
response_iterator = paginator.paginate()

alpha_users = []
for item in response_iterator:
    alpha_users.extend(
        [
            role["RoleName"]
            for role in item["Roles"]
            
            if role["RoleName"].startswith("alpha_user_")
        ]
    )

for alpha_user in alpha_users:
    client.attach_role_policy(
        RoleName=alpha_user,
        PolicyArn="arn:aws:iam::593291632749:policy/airflow-dev-ui-access",
    )
    client.attach_role_policy(
        RoleName=alpha_user,
        PolicyArn="arn:aws:iam::593291632749:policy/airflow-prod-ui-access",
    )
