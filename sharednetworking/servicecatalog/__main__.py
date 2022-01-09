import pulumi_aws as aws
import json
from pulumi_aws import servicecatalog


# Defining config file
with open("./../../config.json") as config_file:
    data = json.load(config_file)

OWNER = "CCOE"
TEMPLATE_URL = data["TEMPLATE_URL"]
servicecatalog_product = aws.servicecatalog.Product(
    "servicecatalog_product",
    owner=OWNER,
    name="vpcvendingmachine",
    type="CLOUD_FORMATION_TEMPLATE",
    provisioning_artifact_parameters=servicecatalog.ProductProvisioningArtifactParametersArgs(
        template_url=TEMPLATE_URL,
        type="CLOUD_FORMATION_TEMPLATE",
    ),
    tags={
        "Environment": "Shared",
        "Name": "vpcvendingmachine",
        "Business-unit": "TBC",
        "Technical-contact": "abc@xyz.com",
        "Privacy-impact": "high",
    },
)

portfolio=aws.servicecatalog.Portfolio("portfolio",
    description="vpccendingmachine-portfolio",
    provider_name=OWNER,
    name= f"vpcvendingmachine-portfolio",
    tags={
        "Environment": "Shared",
        "Name": "vpcvendingmachine-portfolio",
        "Business-unit": "TBC",
        "Technical-contact": "abc@xyz.com",
        "Privacy-impact": "high",
    },
    )
portfolio_association= aws.servicecatalog.ProductPortfolioAssociation("portfolio_association",
    portfolio_id=portfolio.id,
    product_id=servicecatalog_product.id)

portfolio_share=aws.servicecatalog.PortfolioShare("portfolio_share",
    principal_id="arn:aws:organizations::463313787261:organization/o-3ggyjdrq19",
    portfolio_id=portfolio.id,
    type="ORGANIZATION")

portfolio_id_export_ssm=aws.ssm.Parameter("portfolio_id_export_ssm",
    type="String",
    name= "portfolio-id",
    value=portfolio.id)

