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
    Duration,
    RemovalPolicy
)


class AiAgentPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create CodeCommit repository
        repository = codecommit.Repository(
            self, "AiAgentRepo",
            repository_name="ai-agent-repository",
            description="Repository for AI Agent code"
        )

        # Create S3 bucket for test cases and evaluations
        test_bucket = s3.Bucket(
            self, "TestBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create CodeBuild project
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

        # Grant permissions to CodeBuild for Bedrock
        build_project.role.add_to_policy(iam.PolicyStatement(
            actions=[
                "bedrock:*",
            ],
            resources=["*"]
        ))

        # Create CodePipeline
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

        # Create Lambda functions for tools
        tools_function = lambda_.Function(
            self, "ToolsFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_asset("lambda/tools"),
            timeout=Duration.minutes(5)
        )

        # Create CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(
            self, "AiAgentDashboard",
            dashboard_name="ai-agent-metrics"
        )

        # Add metrics to dashboard
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

        # Create Batch compute environment and job queue
        # compute_environment = batch.ComputeEnvironment(
        #     self, "BatchCompute",
        #     compute_resources=batch.ComputeResources(
        #         type=batch.ComputeResourceType.SPOT,
        #         min_vcpus=0,
        #         max_vcpus=16
        #     )
        # )
        compute_environment = batch.CfnComputeEnvironment(
            self, "BatchCompute",
            type="MANAGED",
            compute_resources={
                "type": "SPOT",  # or "EC2", "FARGATE", "FARGATE_SPOT"
                "maxvCpus": 16,
                "minvCpus": 0,
                # "subnets": ["subnet-xxxxx"],  # Replace with your subnet IDs
                # "securityGroupIds": ["sg-xxxxx"],  # Replace with your security group IDs
                "instanceTypes": ["optimal"]  # or specific instance types like ["t3.micro"]
                # "instanceRole": "your-instance-role-arn"  # Replace with your instance role ARN
            },
            # service_role="arn:aws:iam::account:role/service-role/AWSBatchServiceRole",  # Replace with your service role
            state="ENABLED"
        )

        job_queue = batch.JobQueue(
            self, "BatchQueue",
            compute_environments=[
                batch.JobQueueComputeEnvironment(
                    compute_environment=compute_environment,
                    order=1
                )
            ]
        )