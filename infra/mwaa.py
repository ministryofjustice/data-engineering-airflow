from pulumi.resource import ResourceOptions
from pulumi_aws.mwaa import (
    Environment,
    EnvironmentNetworkConfigurationArgs,
    EnvironmentLoggingConfigurationArgs,
    EnvironmentLoggingConfigurationDagProcessingLogsArgs,
    EnvironmentLoggingConfigurationSchedulerLogsArgs,
    EnvironmentLoggingConfigurationTaskLogsArgs,
    EnvironmentLoggingConfigurationWebserverLogsArgs,
    EnvironmentLoggingConfigurationWorkerLogsArgs,
)
from .base import base_name, tagger, stack, mwaa_config, environment_name
from .vpc import securityGroup, private_subnets
from .s3 import bucket, requirementsBucketObject
from .iam.roles import executionRole
from .iam.role_policies import executionRolePolicy

environment = Environment(
    resource_name=base_name,
    airflow_version=mwaa_config["airflow_version"],
    dag_s3_path="dags",
    environment_class=mwaa_config["environment_class"],
    execution_role_arn=executionRole.arn,
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
    opts=ResourceOptions(depends_on=[executionRolePolicy]),
)
