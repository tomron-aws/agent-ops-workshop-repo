# AI Agent Testing Pipeline

This project implements an AWS CDK-based CI/CD pipeline for testing and deploying AI agents. The pipeline includes automated testing, evaluation, and deployment capabilities using various AWS services.

## Architecture Components

- AWS CodePipeline for CI/CD orchestration
- AWS CodeBuild for build and test automation
- Amazon Bedrock for AI agent testing and evaluation
- AWS Batch for test clustering and analysis
- AWS Lambda for tools and external API integration
- Amazon CloudWatch for monitoring
- Amazon Q for user interactions
- Bedrock Knowledge Base integration

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Deploy the CDK stack:
```bash
cdk deploy
```

3. Push your AI agent code to the created CodeCommit repository

## Pipeline Flow

1. Developer pushes code to Git repository
2. CodePipeline triggers the build process
3. Bedrock creates conversational tests
4. AWS Batch processes and clusters tests
5. Tests are executed against the agent
6. Changes are evaluated using LLM
7. Deployment occurs upon approval

## Monitoring

The CloudWatch dashboard provides metrics for:
- Agent invocations
- Latency
- Errors
- Costs

## Security

The pipeline includes:
- S3 bucket encryption
- IAM roles and permissions
- Secure API access