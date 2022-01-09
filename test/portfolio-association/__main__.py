import pulumi_aws as aws
import os
import json

#Environment variable file
with open("./../../config.json") as config_file:
    data = json.load(config_file)

PORTFOLIO_ID = os.environ['PORTFOLIO_ID']
ACCOUNT_ID = os.environ['ACCOUNT_ID']
IAM_USER = data['IAM_USER']

portfolio_association = aws.servicecatalog.PrincipalPortfolioAssociation("portfolio_association",
    portfolio_id=PORTFOLIO_ID,
    principal_arn=f"arn:aws:iam::{ACCOUNT_ID}:user/{IAM_USER}")