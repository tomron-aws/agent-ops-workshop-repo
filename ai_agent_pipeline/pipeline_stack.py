from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_batch as batch,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy,
    CfnResource,
    CfnParameter
)

class AiAgentPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        #parameters
        identity_center_arn = CfnParameter(
            self, "IdentityCenterArn",
            type="String",
            description="The ARN of the IAM Identity Center instance",
            default="",  # Empty string as default value
            allowed_pattern="^$|^arn:[\\w-]+:sso:::instance/(sso)?ins-[a-zA-Z0-9-.]{16}$",  # Allows empty string or valid IAM Identity Center ARN
            constraint_description="Must be a valid IAM Identity Center instance ARN or empty string"
        )

        # Create VPC
        vpc = ec2.Vpc(
            self, "BatchVPC",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Create Security Group
        security_group = ec2.SecurityGroup(
            self, "BatchSecurityGroup",
            vpc=vpc,
            description="Security group for Batch compute environment",
            allow_all_outbound=True
        )

        # Create IAM role for Amazon Q
        # q_service_role = iam.Role(
        #     self, "QServiceRole",
        #     assumed_by=iam.ServicePrincipal("qconnect.amazonaws.com"),
        #     managed_policies=[
        #         iam.ManagedPolicy.from_aws_managed_policy_name("AmazonQDeveloperAccess")
        #     ]
        # )

        # Create Amazon Q Agent
        #ToDo: We will eventualy need to create a role for this as the default can't be edited
        q_agent = CfnResource(
            self, "AIAgent",
            type="AWS::QBusiness::Application",
            properties={
                "Description" : "AgentOps-QBiz-Instance Description",
                "DisplayName" : "AgentOps-QBiz-Instance",
                "IdentityCenterInstanceArn" : identity_center_arn.value_as_string,
                "RoleArn": "arn:aws:iam::239122513475:role/service-role/QBusiness-Application-9iqmk"
            }
        )

        q_agent_index = CfnResource(
            self, "AIAgentIndex",
            type="AWS::QBusiness::Index",
            properties={
                "ApplicationId" : q_agent.ref,
                "DisplayName" : "q_agent_index",
            }
        )

        q_agent_retriever = CfnResource(
            self, "AIAgentRetriever",
            type="AWS::QBusiness::Retriever",
            properties={
                "ApplicationId" : q_agent.ref,
                "Configuration" : {
                    "NativeIndexConfiguration" : {
                        "IndexId" : {
                            "Fn::GetAtt": [q_agent_index.logical_id, "IndexId"]
                        }
                    },
                },
                "DisplayName" : "q_agent_retriever",
                "Type" : "NATIVE_INDEX"
            }
        )

        # amazonq-ignore-next-line
        data_source_bucket = s3.Bucket(
            self, "DataSourceBucket",
            bucket_name="agentops-qbiz-datasource",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create IAM role for QBusiness
        qbusiness_s3_datasource_role = iam.Role(
            self, "QBusinessServiceRole",
            assumed_by=iam.ServicePrincipal("qbusiness.amazonaws.com"),
            description="Role for QBusiness to access S3 data source"
        )

        # Add permissions to access the S3 bucket
        qbusiness_s3_datasource_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:ListBucket",
                "s3:GetBucketLocation"
            ],
            resources=[
                data_source_bucket.bucket_arn,
                f"{data_source_bucket.bucket_arn}/*"
            ]
        ))


        q_agent_s3_data_source = CfnResource(
            self, "AIAgentDataSource",
            type="AWS::QBusiness::DataSource",
            properties={
                "ApplicationId" : q_agent.ref,
                "DisplayName" : "S3-Data-Source",
                "IndexId" : {
                    "Fn::GetAtt": [q_agent_index.logical_id, "IndexId"]
                },
                "RoleArn": qbusiness_s3_datasource_role.role_arn,  # Add this line
                "Configuration": {
                    "type": "S3",
                    "syncMode": "FULL_CRAWL",
                    "connectionConfiguration": {
                        "repositoryEndpointMetadata": {
                        "BucketName": data_source_bucket.bucket_name
                        }
                    },
                    "repositoryConfigurations": {
                        "document": {
                        "fieldMappings": [
                            {
                            "dataSourceFieldName": "content",
                            "indexFieldName": "document_content",
                            "indexFieldType": "STRING"
                            }
                        ]
                        }
                    },
                    "additionalProperties": {
                        "inclusionPatterns": [],
                        "exclusionPatterns": [],
                        "inclusionPrefixes": [],
                        "exclusionPrefixes": [],
                        "aclConfigurationFilePath": "/configs/acl.json",
                        "metadataFilesPrefix": "/metadata/",
                        "maxFileSizeInMegaBytes": "50"
                    }
                }
            }
        )

        # Create IAM roles
        batch_service_role = iam.Role(
            self, "BatchServiceRole",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSBatchServiceRole")
            ]
        )

        # Create instance profile for EC2 instances
        batch_instance_role = iam.Role(
            self, "BatchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2ContainerServiceforEC2Role")
            ]
        )
        # Add this after creating the other IAM roles
        spot_fleet_role = iam.Role(
            self, "SpotFleetRole",
            assumed_by=iam.ServicePrincipal("spotfleet.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2SpotFleetTaggingRole")
            ]
        )


        batch_instance_profile = iam.CfnInstanceProfile(
            self, "BatchInstanceProfile",
            roles=[batch_instance_role.role_name]
        )

        # Your existing repository creation
        repository = codecommit.Repository(
            self, "AiAgentRepo",
            repository_name="ai-agent-repository",
            description="Repository for AI Agent code"
        )

        # Your existing S3 bucket creation
        test_bucket = s3.Bucket(
            self, "TestBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Your existing build project
        build_project = codebuild.PipelineProject(
            self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            environment_variables={
                "TEST_BUCKET": codebuild.BuildEnvironmentVariable(
                    value=test_bucket.bucket_name
                )
            }
        )

        # Grant Bedrock permissions
        build_project.role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:*"],
            resources=["*"]
        ))

        # Create Batch compute environment with the new resources
        compute_environment = batch.CfnComputeEnvironment(
            self, "BatchCompute",
            type="MANAGED",
            compute_resources={
                "type": "SPOT",
                "maxvCpus": 16,
                "minvCpus": 0,
                "subnets": [subnet.subnet_id for subnet in vpc.private_subnets],
                "securityGroupIds": [security_group.security_group_id],
                "instanceTypes": ["optimal"],
                "instanceRole": batch_instance_profile.attr_arn,
                "spotIamFleetRole": spot_fleet_role.role_arn,  # Add this line
                "bidPercentage": 60  # Optional: maximum percentage of On-Demand price to bid
            },
            service_role=batch_service_role.role_arn,
            state="ENABLED"
        )

        # Create Batch job queue
        job_queue = batch.CfnJobQueue(
            self, "BatchQueue",
            compute_environment_order=[{
                "computeEnvironment": compute_environment.attr_compute_environment_arn,
                "order": 1
            }],
            priority=1,
            state="ENABLED"
        )

        # Your existing pipeline creation
        pipeline = codepipeline.Pipeline(
            self, "AiAgentPipeline",
            pipeline_name="ai-agent-pipeline"
        )

        source_output = codepipeline.Artifact()
        build_output = codepipeline.Artifact()

        # Add source stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="CodeCommit_Source",
                    repository=repository,
                    output=source_output,
                    branch="main"
                )
            ]
        )

        # Add build stage
        pipeline.add_stage(
            stage_name="Build",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Build",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output]
                )
            ]
        )

        # Your existing Lambda function
        tools_function = lambda_.Function(
            self, "ToolsFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/tools"),
            timeout=Duration.minutes(5)
        )

        # Your existing CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(
            self, "AiAgentDashboard",
            dashboard_name="ai-agent-metrics"
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Agent Invocations",
                left=[
                    tools_function.metric_invocations(),
                    tools_function.metric_errors()
                ]
            ),
            cloudwatch.GraphWidget(
                title="Agent Latency",
                left=[tools_function.metric_duration()]
            )
        )
