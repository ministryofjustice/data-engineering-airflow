from data_engineering_pulumi_components.utils import Tagger
from pulumi import Config, InvokeOptions, get_stack
from pulumi_aws import get_caller_identity, get_region

from .providers import data_provider

config = Config()
eks_config = config.require_object("eks")
mwaa_config = config.require_object("mwaa")
vpc_config = config.require_object("vpc")

account_id = get_caller_identity(opts=InvokeOptions(provider=data_provider)).account_id

caller_arn = get_caller_identity(opts=InvokeOptions(provider=data_provider)).arn

region = get_region(opts=InvokeOptions(provider=data_provider)).name

stack = get_stack()

base_name = f"airflow-{stack}"

environment_name = stack

tagger = Tagger(environment_name=stack, application="Airflow")
