from constructs import Construct
import os

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
    aws_s3_deployment as s3deploy,
    Duration,
    RemovalPolicy,
    CfnResource,
    CfnParameter,
    CfnOutput
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

        __dirname = os.path.dirname(os.path.realpath(__file__))

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
        #Create bedrock agents for testing
        # Create IAM role for the agents
        agent_role = iam.Role(
            self, "BedrockAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="IAM role for Bedrock agents"
        )

        # Add required policies to the role
        agent_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )

        # Create the first agent using CfnAgent
        bedrock_agent_test = CfnResource(
            self, "TestAgent",
            type="AWS::Bedrock::Agent",
            properties={
                "AgentName": "ContentCreatorAgent",
                "AgentResourceRoleArn": agent_role.role_arn,
                "FoundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Instruction": "You are an agent that tests other Bedrock agents for Quality Assurance.",
                "Description": "Agent specialized in content creation",
                "IdleSessionTTLInSeconds": 1800
            }
        )

        bedrock_agent_functional = CfnResource(
            self, "FunctionalAgent",
            type="AWS::Bedrock::Agent",
            properties={
                "AgentName": "DataAnalystAgent",
                "AgentResourceRoleArn": agent_role.role_arn,
                "FoundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
                "Instruction": "You are a travel agent. You assist customers in booking and modifying flights",
                "Description": "Agent specialized in flight booking",
                "IdleSessionTTLInSeconds": 1800
            }
        )

        # Output the agent IDs
        CfnOutput(self, "FirstAgentId", value=bedrock_agent_test.ref)
        CfnOutput(self, "SecondAgentId", value=bedrock_agent_functional.ref)

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
        q_agent_plugin = CfnResource(
            self, "AIAgentPlugin",
            type="AWS::QBusiness::Plugin",
            properties={
                "ApplicationId" : q_agent.ref,
                "AuthConfiguration" : {
                    "NoAuthConfiguration": {}
                },
                "CustomPluginConfiguration" : {
                    "ApiSchema" : {
                        
                        "Payload" : """{
                            "openapi": "3.0.0",
                            "info": {
                                "title": "FastAPI",
                                "version": "0.1.0"
                            },
                            "servers": [
                                {
                                "url": "https://dj3a2w5zbcgq8.cloudfront.net"
                                }
                            ],
                            "paths": {
                                "/api/chat/": {
                                "post": {
                                    "tags": [
                                    "chat_router"
                                    ],
                                    "summary": "Chat",
                                    "description": "This API is used by a Financial Analyst  to provide clients' financial goals, stock information and S&P 500 and DOW Jones reqlated queries.The API interacts with SearchClient, ClientList, ClientDetail, StockInfo, Index_Tickers, GoalServicePopularGoals",
                                    "operationId": "chat_api_chat__post",
                                    "requestBody": {
                                    "content": {
                                        "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ChatRequest"
                                        }
                                        }
                                    },
                                    "required": true
                                    },
                                    "responses": {
                                    "200": {
                                        "description": "Successful Response",
                                        "content": {
                                        "application/json": {
                                            "schema": {
                                            "$ref": "#/components/schemas/ChatResponse"
                                            }
                                        }
                                        }
                                    },
                                    "422": {
                                        "description": "Validation Error",
                                        "content": {
                                        "application/json": {
                                            "schema": {
                                            "$ref": "#/components/schemas/HTTPValidationError"
                                            }
                                        }
                                        }
                                    }
                                    }
                                }
                                }
                            },
                            "components": {
                                "schemas": {
                                "ChatRequest": {
                                    "type": "object",
                                    "title": "ChatRequest",
                                    "properties": {
                                    "prompt": {
                                        "type": "string",
                                        "title": "Prompt"
                                    }
                                    },
                                    "required": [
                                    "prompt"
                                    ]
                                },
                                "ChatResponse": {
                                    "type": "object",
                                    "title": "ChatResponse",
                                    "properties": {
                                    "response": {
                                        "type": "string",
                                        "title": "Response"
                                    }
                                    },
                                    "required": [
                                    "response"
                                    ]
                                },
                                "HTTPValidationError": {
                                    "type": "object",
                                    "title": "HTTPValidationError",
                                    "properties": {
                                    "detail": {
                                        "type": "array",
                                        "title": "Detail",
                                        "items": {
                                        "$ref": "#/components/schemas/ValidationError"
                                        }
                                    }
                                    }
                                },
                                "ValidationError": {
                                    "type": "object",
                                    "title": "ValidationError",
                                    "properties": {
                                    "loc": {
                                        "type": "array",
                                        "title": "Location",
                                        "items": {
                                        "anyOf": [
                                            {
                                            "type": "string"
                                            },
                                            {
                                            "type": "integer"
                                            }
                                        ]
                                        }
                                    },
                                    "msg": {
                                        "type": "string",
                                        "title": "Message"
                                    },
                                    "type": {
                                        "type": "string",
                                        "title": "Error Type"
                                    }
                                    },
                                    "required": [
                                    "loc",
                                    "msg",
                                    "type"
                                    ]
                                }
                                }
                            }
                            }"""
                    },
                    "ApiSchemaType" : "OPEN_API_V3",
                    "Description" : "plugin description"
                },
                "DisplayName" : "q-biz-plugin",
                "Type" : "CUSTOM"
            }
        )

        # Create IAM role for Q Business Web Experience
        web_experience_role = iam.Role(
            self, "QBusinessWebExperienceRole",
            assumed_by=iam.ServicePrincipal("qbusiness.amazonaws.com"),
            description="Role for Q Business Web Experience"
        )

        # Add trust relationship conditions
        web_experience_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("qbusiness.amazonaws.com")],
                actions=["sts:AssumeRole"],
                conditions={
                    "StringEquals": {
                        "aws:SourceAccount": Stack.of(self).account
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:qbusiness:{Stack.of(self).region}:{Stack.of(self).account}:application/{q_agent.ref}"
                    }
                }
            )
        )

        # Add required permissions for web experience with IAM Identity Center
        web_experience_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "qbusiness:Chat",
                    "qbusiness:ChatSync",
                    "qbusiness:ListMessages",
                    "qbusiness:ListConversations",
                    "qbusiness:PutFeedback",
                    "qbusiness:DeleteConversation",
                    "qbusiness:GetWebExperience",
                    "qbusiness:GetApplication",
                    "qbusiness:ListPlugins",
                    "qbusiness:ListPluginActions",
                    "qbusiness:GetChatControlsConfiguration",
                    "qbusiness:ListRetrievers",
                    "qbusiness:ListAttachments",
                    "qbusiness:GetMedia"
                ],
                resources=[f"arn:aws:qbusiness:{Stack.of(self).region}:{Stack.of(self).account}:application/{q_agent.ref}"]
            )
        )

        # Add plugin discovery permissions
        web_experience_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "qbusiness:ListPluginTypeMetadata",
                    "qbusiness:ListPluginTypeActions"
                ],
                resources=["*"]
            )
        )

        # Add retriever permissions
        web_experience_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["qbusiness:GetRetriever"],
                resources=[
                    f"arn:aws:qbusiness:{Stack.of(self).region}:{Stack.of(self).account}:application/{q_agent.ref}",
                    f"arn:aws:qbusiness:{Stack.of(self).region}:{Stack.of(self).account}:application/{q_agent.ref}/retriever/*"
                ]
            )
        )
        # Create Web Experience for Q Business application
        q_agent_web_experience = CfnResource(
            self, "AIAgentWebExperience",
            type="AWS::QBusiness::WebExperience",
            properties={
                "ApplicationId": q_agent.ref,
                "RoleArn": web_experience_role.role_arn
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
        buildspec_bucket = s3.Bucket(
            self, "BuildspecBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            enforce_ssl=True
        )

        # Copy the asset to the buildspec bucket
        deployment = s3deploy.BucketDeployment(self, "DeployFiles",
            sources=[s3deploy.Source.asset(f"{__dirname}/../ai_agent_pipeline/assets/")],
            destination_bucket=buildspec_bucket
        )

        # Your existing build project
        build_project = codebuild.Project(
            self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            source=codebuild.Source.s3(
                bucket=buildspec_bucket,
                path=""
            ),
            environment_variables={
                "TEST_BUCKET": codebuild.BuildEnvironmentVariable(
                    value=buildspec_bucket.bucket_name
                )
            }
        )

        buildspec_bucket.grant_read(build_project)
        buildspec_bucket.grant_read(build_project)
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
