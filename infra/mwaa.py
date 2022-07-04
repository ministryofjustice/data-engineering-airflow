from pulumi.resource import ResourceOptions
from pulumi_aws.mwaa import (
    Environment,
    EnvironmentLoggingConfigurationArgs,
    EnvironmentLoggingConfigurationDagProcessingLogsArgs,
    EnvironmentLoggingConfigurationSchedulerLogsArgs,
    EnvironmentLoggingConfigurationTaskLogsArgs,
    EnvironmentLoggingConfigurationWebserverLogsArgs,
    EnvironmentLoggingConfigurationWorkerLogsArgs,
    EnvironmentNetworkConfigurationArgs,
)
from pulumi_aws.ses import EmailIdentity

from .base import base_name, environment_name, mwaa_config, stack, tagger
from .iam.role_policies import executionRolePolicy
from .iam.roles import executionRole
from .iam.smtp_user import access_key
from .s3 import bucket, requirementsBucketObject
from .vpc import private_subnets, securityGroup

smtp_user = access_key.id
smtp_password = access_key.ses_smtp_password_v4
smtp_config = mwaa_config['smtp']

ses_email = EmailIdentity(
    resource_name="data_engineering_email",
    email="dataengineering@digital.justice.gov.uk",
)

environment = Environment(
    resource_name=base_name,
    airflow_version=mwaa_config["airflow_version"],
    dag_s3_path="dags",
    environment_class=mwaa_config["environment_class"],
    execution_role_arn=executionRole.arn,
    airflow_configuration_options={
        "smtp.smtp_host": smtp_config['smtp_host'],
        "smtp.smtp_port": smtp_config['smtp_port'],
        "smtp.smtp_user": smtp_user,
        "smtp.smtp_password": smtp_password,
        "smtp.smtp_mail_from": smtp_config['smtp_mail_from'],
        "smtp.smtp_starttls": True,
    },
    logging_configuration=EnvironmentLoggingConfigurationArgs(
        dag_processing_logs=EnvironmentLoggingConfigurationDagProcessingLogsArgs(
            enabled=True, log_level="INFO"
        ),
        scheduler_logs=EnvironmentLoggingConfigurationSchedulerLogsArgs(
            enabled=True, log_level="INFO"
        ),
        task_logs=EnvironmentLoggingConfigurationTaskLogsArgs(
            enabled=True, log_level="INFO"
        ),
        webserver_logs=EnvironmentLoggingConfigurationWebserverLogsArgs(
            enabled=True, log_level="INFO"
        ),
        worker_logs=EnvironmentLoggingConfigurationWorkerLogsArgs(
            enabled=True, log_level="INFO"
        ),
    ),
    max_workers=mwaa_config.get("max_workers"),
    min_workers=mwaa_config.get("min_workers"),
    name=environment_name,
    source_bucket_arn=bucket.arn,
    network_configuration=EnvironmentNetworkConfigurationArgs(
        security_group_ids=[securityGroup.id],
        subnet_ids=[private_subnet.id for private_subnet in private_subnets[:2]],
    ),
    requirements_s3_path=requirementsBucketObject.key,
    requirements_s3_object_version=requirementsBucketObject.version_id,
    tags=tagger.create_tags(stack),
    webserver_access_mode="PUBLIC_ONLY",
    opts=ResourceOptions(depends_on=[executionRolePolicy, ses_email]),
)
