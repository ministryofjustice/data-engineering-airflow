from data_engineering_pulumi_components.utils import Tagger
from pulumi import Config, get_stack
from pulumi_aws import get_caller_identity, get_region

config = Config()
eks_config = config.require_object("eks")
mwaa_config = config.require_object("mwaa")
vpc_config = config.require_object("vpc")

account_id = get_caller_identity().account_id

# caller_arn = Config("aws").require_object("assume_role")["role_arn"]

region = get_region().name

stack = get_stack()

base_name = f"airflow-{stack}"

environment_name = stack

tagger = Tagger(environment_name=stack, application="Airflow")
