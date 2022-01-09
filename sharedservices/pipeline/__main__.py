import pulumi
import pulumi_aws as aws
from pulumi import export, ResourceOptions
import json

# Buildspec SharedNetworking file
with open("./buildspec_sharednetworking.yaml", mode="r") as buildspec_sharednetworking:
    buildspec_sharednetworking = buildspec_sharednetworking.read()


# Buildspec Member accounts file
with open("./buildspec_memberaccounts.yaml", mode="r") as buildspec_memberaccounts:
    buildspec_memberaccounts = buildspec_memberaccounts.read()


with open("./buildspec_update_servicecatalog.yaml", mode="r") as buildspec_update_servicecatalog:
    buildspec_update_servicecatalog = buildspec_update_servicecatalog.read()


# Defining config file
with open("./../../config.json") as config_file:
    data = json.load(config_file)

############################################################################################################
#######################################Declaring Env Variables##############################################


ACCOUNT_LIST = ["dev", "test", "prod"]
SHARED_NETWORKING_ACCOUNT_STAGE_ACTION = "up"
REPO_NAME = data["REPO_NAME"]
SOURCE_VERSION = data["SOURCE_VERSION"]
STATE_BUCKET = data["STATE_BUCKET"]
TEMPLATE_BUCKET = data["TEMPLATE_BUCKET"]
SHAREDNETWORKING_ACCOUNT_ID = data["ACCOUNT"]["SHARED_NETWORKING"]["ID"]
SHAREDSERVICES_ACCOUNT_ID = data["ACCOUNT"]["SHARED_SERVICES"]["ID"]
DEV = data["ACCOUNT"]["DEV"]["ID"]
TEST = data["ACCOUNT"]["TEST"]["ID"]
PROD = data["ACCOUNT"]["PROD"]["ID"]

############################################################################################################
################################Creating Codebuild role policy##############################################
Account_List = ["dev1", "dev2", "dev3"]


codebuild_role_policy = aws.iam.Policy(
    "codebuildRolePolicy",
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "CodeBuildDefaultPolicy",
                    "Effect": "Allow",
                    "Action": ["codebuild:*", "iam:PassRole"],
                    "Resource": "*",
                },
                {
                    "Sid": "CloudWatchLogsAccessPolicy",
                    "Effect": "Allow",
                    "Action": [
                        "logs:FilterLogEvents",
                        "logs:GetLogEvents",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "CodeCommitAccessPolicy",
                    "Effect": "Allow",
                    "Action": [
                        "codecommit:GitPull",
                        "codecommit:GetBranch",
                        "codecommit:GetCommit",
                        "codecommit:GetRepository",
                        "codecommit:ListBranches",
                        "codecommit:ListRepositories",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "S3AccessPolicy",
                    "Effect": "Allow",
                    "Action": [
                        "s3:CreateBucket",
                        "s3:GetObject",
                        "s3:ListObject",
                        "s3:ListObjectV2",
                        "s3:PutObject",
                        "s3:ListBuckets"
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "S3BucketIdentity",
                    "Effect": "Allow",
                    "Action": ["s3:GetBucketAcl", "s3:GetBucketLocation"],
                    "Resource": "*",
                },
                {
                    "Sid": "AssumeRole",
                    "Effect": "Allow",
                    "Action": ["sts:AssumeRole"],
                    "Resource": [
                        "arn:aws:iam::{}:role/vpcvendingmachine_cross_account_codebuild_role".format(
                            SHAREDNETWORKING_ACCOUNT_ID
                        ),
                        "arn:aws:iam::{}:role/vpcvendingmachine_cross_account_codebuild_role".format(DEV),
                        "arn:aws:iam::{}:role/vpcvendingmachine_cross_account_codebuild_role".format(TEST),
                        "arn:aws:iam::{}:role/vpcvendingmachine_cross_account_codebuild_role".format(PROD),
                    ],
                },
            ],
        }
    ),
)
############################################################################################################
#######################################Creating Codebuild role##############################################
codebuild_role = aws.iam.Role(
    "codebuildRole",
    managed_policy_arns=[codebuild_role_policy.arn],
    name="Codebuild_role_crossaccount_",
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
""",
)
############################################################################################################
#########################################Creating Artifact Bucket###########################################
codepipeline_bucket = aws.s3.Bucket(
    "codepipelineBucket",
    acl="private",
    tags={"Name": "dinesh-pulumi-codepipeline-bucket"},
)
###########################################################################################################
##############################Creating Codebuild project SharedNetworking##################################
codebuild_project_sharednetworking = aws.codebuild.Project(
    "CodebuildProjectSharednetworking",
    description="codebuild_project_sharednetworking",
    #name="cross_account_codebuild_project_sharednetworking_" + env,
    name="vpcvendingmachine_codebuild_project_sharednetworking",
    build_timeout=30,
    service_role=codebuild_role.arn,
    artifacts=aws.codebuild.ProjectArtifactsArgs(
        type="NO_ARTIFACTS",
    ),
    environment=aws.codebuild.ProjectEnvironmentArgs(
        compute_type="BUILD_GENERAL1_SMALL",
        image="aws/codebuild/standard:3.0",
        type="LINUX_CONTAINER",
        image_pull_credentials_type="CODEBUILD",
        environment_variables=[
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="PULUMI_CONFIG_PASSPHRASE", value=""
            ),
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="ACCOUNT_ID", value=SHAREDSERVICES_ACCOUNT_ID
            ),
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="STATE_BUCKET", value=STATE_BUCKET
            ),
        ],
    ),
    logs_config=aws.codebuild.ProjectLogsConfigArgs(
        cloudwatch_logs=aws.codebuild.ProjectLogsConfigCloudwatchLogsArgs(
            group_name="vpcvendingmachine-codebuild-sharednetworking-log-group",
            stream_name="vpcvendingmachine-codebuild-sharednetworking-log-stream",
        )
    ),
    source=aws.codebuild.ProjectSourceArgs(
        type="CODECOMMIT",
        location="https://git-codecommit.ap-southeast-2.amazonaws.com/v1/repos/"
        + REPO_NAME,
        git_clone_depth=1,
        git_submodules_config=aws.codebuild.ProjectSourceGitSubmodulesConfigArgs(
            fetch_submodules=True,
        ),
        buildspec=buildspec_sharednetworking,
    ),
    source_version=SOURCE_VERSION,
    tags={
        "Environment": "SharedNetworking",
        "Name": "cross_account_codebuild_project_sharednetworking",
        "Business-unit": "TBC",
        "Technical-contact": "abc@xyz.com",
        "Privacy-impact": "high",},
)

############################################################################################################
###############################Creating Codebuild project member accounts##################################
codebuild_project_memberaccounts = aws.codebuild.Project(
    "CodebuildProjectMemberaccounts",
    description="codebuild_project_memberaccounts",
    name="vpcvendingmachine_codebuild_project_memberaccounts",
    build_timeout=30,
    service_role=codebuild_role.arn,
    artifacts=aws.codebuild.ProjectArtifactsArgs(
        type="NO_ARTIFACTS",
    ),
    environment=aws.codebuild.ProjectEnvironmentArgs(
        compute_type="BUILD_GENERAL1_SMALL",
        image="aws/codebuild/standard:3.0",
        type="LINUX_CONTAINER",
        image_pull_credentials_type="CODEBUILD",
        environment_variables=[
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="PULUMI_CONFIG_PASSPHRASE", value=""
            ),
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="SHAREDNETWORKING_ACCOUNT_ID", value=SHAREDNETWORKING_ACCOUNT_ID
            ),
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="STATE_BUCKET", value=STATE_BUCKET
            ),
        ],
    ),
    logs_config=aws.codebuild.ProjectLogsConfigArgs(
        cloudwatch_logs=aws.codebuild.ProjectLogsConfigCloudwatchLogsArgs(
            group_name="vpcvendingmachine-codebuild-memberaccounts-log-group",
            stream_name="vpcvendingmachine-codebuild-memberaccounts-log-stream",
        )
    ),
    source=aws.codebuild.ProjectSourceArgs(
        type="CODECOMMIT",
        location="https://git-codecommit.ap-southeast-2.amazonaws.com/v1/repos/"
        + REPO_NAME,
        git_clone_depth=1,
        git_submodules_config=aws.codebuild.ProjectSourceGitSubmodulesConfigArgs(
            fetch_submodules=True,
        ),
        buildspec=buildspec_memberaccounts,
    ),
    source_version=SOURCE_VERSION,
    tags={
        "Environment": "SharedNetworking",
        "Name": "vpcvendingmachine_codebuild_project_memberaccounts",
        "Business-unit": "TBC",
        "Technical-contact": "abc@xyz.com",
        "Privacy-impact": "high",},
)

############################################################################################################
###############################Creating Codebuild project update servicecatalog##################################
codebuild_project_update_service_catalog = aws.codebuild.Project(
    "CodebuildProjectUpdateServiceCatalog",
    description="vpcvendingmachine_codebuild_project_update_service_catalog",
    name="vpcvendingmachine_codebuild_project_update_service_catalog",
    build_timeout=30,
    service_role=codebuild_role.arn,
    artifacts=aws.codebuild.ProjectArtifactsArgs(
        type="NO_ARTIFACTS",
    ),
    environment=aws.codebuild.ProjectEnvironmentArgs(
        compute_type="BUILD_GENERAL1_SMALL",
        image="aws/codebuild/standard:3.0",
        type="LINUX_CONTAINER",
        image_pull_credentials_type="CODEBUILD",
        environment_variables=[
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="PULUMI_CONFIG_PASSPHRASE", value=""
            ),
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="SHAREDNETWORKING_ACCOUNT_ID", value=SHAREDNETWORKING_ACCOUNT_ID
            ),
            aws.codebuild.ProjectEnvironmentEnvironmentVariableArgs(
                name="STATE_BUCKET", value=STATE_BUCKET
            ),
        ],
    ),
    logs_config=aws.codebuild.ProjectLogsConfigArgs(
        cloudwatch_logs=aws.codebuild.ProjectLogsConfigCloudwatchLogsArgs(
            group_name="vpcvendingmachine-update-service-catalog-log-group",
            stream_name="vpcvendingmachine-update-service-catalog-log-stream",
        )
    ),
    source=aws.codebuild.ProjectSourceArgs(
        type="CODECOMMIT",
        location="https://git-codecommit.ap-southeast-2.amazonaws.com/v1/repos/"
        + REPO_NAME,
        git_clone_depth=1,
        git_submodules_config=aws.codebuild.ProjectSourceGitSubmodulesConfigArgs(
            fetch_submodules=True,
        ),
        buildspec=buildspec_update_servicecatalog,
    ),
    source_version=SOURCE_VERSION,
    tags={"Environment": "SharedNetworking",
        "Name": "vpcvendingmachine_codebuild_project_memberaccounts",
        "Business-unit": "TBC",
        "Technical-contact": "abc@xyz.com",
        "Privacy-impact": "high",},
)

############################################################################################################
####################################Creating Codepipeline Policy############################################
codepipeline_policy = aws.iam.Policy(
    "codepipelinePolicy",
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["s3:*"], "Resource": ["*"]},
                {
                    "Effect": "Allow",
                    "Action": [
                        "codebuild:*",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "codecommit:*",
                    ],
                    "Resource": "arn:aws:codecommit:ap-southeast-2:{}:{}".format(
                        SHAREDSERVICES_ACCOUNT_ID, REPO_NAME
                    ),
                },
            ],
        }
    ),
)
############################################################################################################
####################################Creating Codepipeline Role##############################################
codepipeline_role = aws.iam.Role(
    "codepipelineRole",
    managed_policy_arns=[codepipeline_policy.arn],
    name="Codepipeline_role",
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codepipeline.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
""",
)

############################################################################################################
####################################Creating Codepipeline Role##############################################
codepipeline = aws.codepipeline.Pipeline(
    "codepipeline",
    name="vpcvendingmachine_cross_account_codepipeline",
    role_arn=codepipeline_role.arn,
    artifact_store=aws.codepipeline.PipelineArtifactStoreArgs(
        location=codepipeline_bucket.bucket,
        type="S3",
    ),
    stages=[
        aws.codepipeline.PipelineStageArgs(
            name="Source",
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    name="Source",
                    category="Source",
                    owner="AWS",
                    provider="CodeCommit",
                    version="1",
                    output_artifacts=["source_output"],
                    configuration={
                        "RepositoryName": REPO_NAME,
                        "BranchName": SOURCE_VERSION,
                    },
                )
            ],
        ),
        aws.codepipeline.PipelineStageArgs(
            name="DeployInfrastructure-SharedNetworking",
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    name="DeployInfrastructure",
                    category="Build",
                    owner="AWS",
                    provider="CodeBuild",
                    input_artifacts=["source_output"],
                    version="1",
                    configuration={
                        "ProjectName": codebuild_project_sharednetworking.name,
                        "EnvironmentVariables": json.dumps(
                            [
                                {
                                    "name": "PULUMI_CONFIG_PASSPHRASE",
                                    "value": "",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "PULUMI_CONFIG_PASSPHRASE_FILE",
                                    "value": "",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACCOUNT",
                                    "value": "sharednetworking",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "STACK",
                                    "value": "sharednetworking-vpc",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACCOUNT_ID",
                                    "value": SHAREDNETWORKING_ACCOUNT_ID,
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACTION",
                                    "value": SHARED_NETWORKING_ACCOUNT_STAGE_ACTION,
                                    "type": "PLAINTEXT",
                                },
                            ]
                        ),
                    },
                )
            ],
        ),
        aws.codepipeline.PipelineStageArgs(
            name="Update-Service-Catalog-Template",
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    name="Update-Service-Catalog-Template",
                    category="Build",
                    owner="AWS",
                    provider="CodeBuild",
                    input_artifacts=["source_output"],
                    version="1",
                    configuration={
                        "ProjectName": codebuild_project_update_service_catalog.name,
                        "EnvironmentVariables": json.dumps(
                            [
                                {
                                    "name": "TEMPLATE_BUCKET",
                                    "value": TEMPLATE_BUCKET,
                                    "type": "PLAINTEXT",
                                },
                                
                            ]
                        ),
                    },
                )
            ],
        ),
        aws.codepipeline.PipelineStageArgs(
            name="Deploy-Service-Catalog",
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    name="Deploy-Service-Catalog",
                    category="Build",
                    owner="AWS",
                    provider="CodeBuild",
                    input_artifacts=["source_output"],
                    version="1",
                    configuration={
                        "ProjectName": codebuild_project_sharednetworking.name,
                        "EnvironmentVariables": json.dumps(
                            [
                                {
                                    "name": "PULUMI_CONFIG_PASSPHRASE",
                                    "value": "",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "PULUMI_CONFIG_PASSPHRASE_FILE",
                                    "value": "",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACCOUNT",
                                    "value": "sharednetworking",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "STACK",
                                    "value": "servicecatalog",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACCOUNT_ID",
                                    "value": SHAREDNETWORKING_ACCOUNT_ID,
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACTION",
                                    "value": "up",
                                    "type": "PLAINTEXT",
                                },
                            ]
                        ),
                    },
                )
            ],
        ),
        aws.codepipeline.PipelineStageArgs(
            name="Principal-Portfolio-Association",
            actions=[
                aws.codepipeline.PipelineStageActionArgs(
                    name=account,
                    category="Build",
                    owner="AWS",
                    provider="CodeBuild",
                    input_artifacts=["source_output"],
                    version="1",
                    configuration={
                        "ProjectName": codebuild_project_memberaccounts.name,
                        "EnvironmentVariables": json.dumps(
                            [
                                {
                                    "name": "PULUMI_CONFIG_PASSPHRASE",
                                    "value": "",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "PULUMI_CONFIG_PASSPHRASE_FILE",
                                    "value": "",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACCOUNT",
                                    "value": account,
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "STACK",
                                    "value": f"{account}-portfolio-association",
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACCOUNT_ID",
                                    "value": data["ACCOUNT"][account.upper()]["ID"],
                                    "type": "PLAINTEXT",
                                },
                                {
                                    "name": "ACTION",
                                    "value": "up",
                                    "type": "PLAINTEXT",
                                },
                            ]
                        ),
                    },
                )
                for account in ACCOUNT_LIST
            ],
        ),
    ],
)