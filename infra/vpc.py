from pulumi import ResourceOptions
from pulumi_aws import get_availability_zones
from pulumi_aws.cloudwatch import LogGroup
from pulumi_aws.ec2 import (
    Eip,
    FlowLog,
    InternetGateway,
    NatGateway,
    Route,
    RouteTable,
    RouteTableAssociation,
    SecurityGroup,
    SecurityGroupRule,
    Subnet,
    Vpc,
    VpnGateway,
)
from pulumi_aws.ec2transitgateway import TransitGateway, VpcAttachment

from .base import base_name, config, tagger
from .iam.roles import flowLogRole

vpc_config = config.require_object("vpc")

vpc = Vpc(
    resource_name=base_name,
    cidr_block=vpc_config["cidr_block"],
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags=tagger.create_tags(base_name),
)

# this is called virtual private gateway in the control panel
vpnGateway = VpnGateway(
    resource_name=base_name,
    vpc_id=vpc.id,
    tags=tagger.create_tags(base_name),
    opts=ResourceOptions(parent=vpc),
)

internetGateway = InternetGateway(
    resource_name=base_name,
    tags=tagger.create_tags(base_name),
    vpc_id=vpc.id,
    opts=ResourceOptions(parent=vpc),
)

transitGateway = TransitGateway.get(
    resource_name=vpc_config["transit_gateway"]["name"],
    id=vpc_config["transit_gateway"]["id"],
)

publicRouteTable = RouteTable(
    resource_name=f"{base_name}-public",
    vpc_id=vpc.id,
    tags=tagger.create_tags(f"{base_name}-public"),
    opts=ResourceOptions(parent=vpc),
)
defaultPublicRoute = Route(
    resource_name=f"{base_name}-public",
    destination_cidr_block="0.0.0.0/0",
    gateway_id=internetGateway.id,
    route_table_id=publicRouteTable.id,
    opts=ResourceOptions(parent=publicRouteTable),
)

securityGroup = SecurityGroup(
    resource_name=base_name,
    name=base_name,
    vpc_id=vpc.id,
    opts=ResourceOptions(parent=vpc),
)
ingressRule = SecurityGroupRule(
    resource_name=f"{base_name}-ingress",
    from_port=0,
    protocol="all",
    security_group_id=securityGroup.id,
    source_security_group_id=securityGroup.id,
    to_port=65535,
    type="ingress",
    opts=ResourceOptions(parent=securityGroup),
)
egressRule = SecurityGroupRule(
    resource_name=f"{base_name}-egress",
    cidr_blocks=["0.0.0.0/0"],
    from_port=0,
    protocol="all",
    security_group_id=securityGroup.id,
    to_port=65535,
    type="egress",
    opts=ResourceOptions(parent=securityGroup),
)

available = get_availability_zones(state="available")

public_subnets = []
private_subnets = []

for availability_zone, public_cidr_block, private_cidr_block in zip(
    available.names,
    vpc_config["public_subnets"]["cidr_blocks"],
    vpc_config["private_subnets"]["cidr_blocks"],
):
    publicSubnet = Subnet(
        resource_name=f"{base_name}-public-{availability_zone}",
        availability_zone=availability_zone,
        cidr_block=public_cidr_block,
        map_public_ip_on_launch=True,
        vpc_id=vpc.id,
        tags=tagger.create_tags(f"{base_name}-public-{availability_zone}"),
        opts=ResourceOptions(parent=vpc),
    )
    public_subnets.append(publicSubnet)
    privateSubnet = Subnet(
        resource_name=f"{base_name}-private-{availability_zone}",
        availability_zone=availability_zone,
        cidr_block=private_cidr_block,
        map_public_ip_on_launch=False,
        vpc_id=vpc.id,
        tags=tagger.create_tags(f"{base_name}-private-{availability_zone}"),
        opts=ResourceOptions(parent=vpc),
    )
    private_subnets.append(privateSubnet)
    natGatewayEip = Eip(
        resource_name=f"{base_name}-{availability_zone}",
        vpc=True,
        tags=tagger.create_tags(f"{base_name}-{availability_zone}"),
        opts=ResourceOptions(
            depends_on=[internetGateway], parent=internetGateway, protect=True
        ),
    )
    natGateway = NatGateway(
        resource_name=f"{base_name}-{availability_zone}",
        allocation_id=natGatewayEip.id,
        subnet_id=publicSubnet.id,
        tags=tagger.create_tags(f"{base_name}-{availability_zone}"),
        opts=ResourceOptions(parent=publicSubnet),
    )
    publicRouteTableAssociation = RouteTableAssociation(
        resource_name=f"{base_name}-public-{availability_zone}",
        route_table_id=publicRouteTable.id,
        subnet_id=publicSubnet.id,
        opts=ResourceOptions(parent=publicRouteTable),
    )
    privateRouteTable = RouteTable(
        resource_name=f"{base_name}-private-{availability_zone}",
        vpc_id=vpc.id,
        propagating_vgws=[vpnGateway.id],
        tags=tagger.create_tags(f"{base_name}-private-{availability_zone}"),
        opts=ResourceOptions(parent=privateSubnet),
    )
    defaultPrivateRoute = Route(
        resource_name=f"{base_name}-private-{availability_zone}",
        destination_cidr_block="0.0.0.0/0",
        nat_gateway_id=natGateway.id,
        route_table_id=privateRouteTable.id,
        opts=ResourceOptions(parent=privateRouteTable),
    )
    privateRouteTableAssociation = RouteTableAssociation(
        resource_name=f"{base_name}-private-{availability_zone}",
        route_table_id=privateRouteTable.id,
        subnet_id=privateSubnet.id,
        opts=ResourceOptions(parent=privateRouteTable),
    )
    if vpc_config["transit_gateway"].get("routes"):
        for route in vpc_config["transit_gateway"]["routes"]:
            transitGatewayPrivateRoute = Route(
                resource_name=f"{base_name}-private-{availability_zone}-{route['name']}",
                destination_cidr_block=route["cidr_block"],
                transit_gateway_id=transitGateway.id,
                route_table_id=privateRouteTable.id,
                opts=ResourceOptions(
                    depends_on=transitGateway, parent=privateRouteTable
                ),
            )

transitGatewayVpcAttachment = VpcAttachment(
    resource_name=base_name,
    dns_support="enable",
    subnet_ids=[private_subnet.id for private_subnet in private_subnets],
    transit_gateway_default_route_table_association=True,
    transit_gateway_default_route_table_propagation=True,
    transit_gateway_id=transitGateway.id,
    vpc_id=vpc.id,
    tags=tagger.create_tags(base_name),
    opts=ResourceOptions(
        depends_on=[transitGateway].extend(private_subnets), parent=vpc
    ),
)

flowLogGroup = LogGroup(
    resource_name=f"{base_name}-vpc-flow-log",
    name=f"{base_name}-vpc-flow-log",
    retention_in_days=400,
    tags=tagger.create_tags(f"{base_name}-vpc-flow-log"),
)
flowLog = FlowLog(
    resource_name=base_name,
    iam_role_arn=flowLogRole.arn,
    log_destination=flowLogGroup.arn,
    traffic_type="ALL",
    vpc_id=vpc.id,
    tags=tagger.create_tags(base_name),
    opts=ResourceOptions(parent=vpc),
)
