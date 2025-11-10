# Bedrock Access Gateway Architecture

## Overview
OpenAI-Compatible API Proxy for Amazon Bedrock

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Bedrock Access Gateway                            │
│                        OpenAI-Compatible API Proxy                          │
└─────────────────────────────────────────────────────────────────────────────┘

                                 Internet
                                    │
                                    │ HTTP/80
                                    ▼
                        ┌─────────────────────────┐
                        │  Application Load       │
                        │  Balancer (ALB)         │
                        │  - Internet-facing      │
                        │  - Security Group       │
                        └─────────────────────────┘
                                    │
                                    │ Target Group
                                    ▼
                        ┌─────────────────────────┐
                        │  Lambda Function        │
                        │  - Container Image      │
                        │  - 1024MB Memory        │
                        │  - 600s Timeout         │
                        │  - ARM64 Architecture   │
                        └─────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
        │ Amazon Bedrock  │ │  Secrets    │ │   CloudWatch    │
        │ - InvokeModel   │ │  Manager    │ │   Logs          │
        │ - ListModels    │ │ - API Keys  │ │ - Function Logs │
        │ - Streaming     │ │             │ │                 │
        └─────────────────┘ └─────────────┘ └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              VPC (10.250.0.0/16)                            │
│  ┌─────────────────────────┐           ┌─────────────────────────┐          │
│  │   Public Subnet 1       │           │   Public Subnet 2       │          │
│  │   10.250.0.0/24         │           │   10.250.1.0/24         │          │
│  │   AZ-1                  │           │   AZ-2                  │          │
│  │                         │           │                         │          │
│  │   ┌─────────────────┐   │           │   ┌─────────────────┐   │          │
│  │   │      ALB        │   │           │   │      ALB        │   │          │
│  │   │   (Multi-AZ)    │   │           │   │   (Multi-AZ)    │   │          │
│  │   └─────────────────┘   │           │   └─────────────────┘   │          │
│  └─────────────────────────┘           └─────────────────────────┘          │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────────┐                                  │
│                    │  Internet Gateway   │                                  │
│                    └─────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Components

### Core Infrastructure
- **VPC** with public subnets across 2 availability zones for high availability
- **Application Load Balancer** (internet-facing) to distribute traffic
- **Lambda function** (containerized) that acts as the API proxy
- **Internet Gateway** for public internet access

### Key Services
- **Amazon Bedrock** for foundation model inference
- **AWS Secrets Manager** for secure API key storage
- **CloudWatch** for logging and monitoring

### Security & Access
- Lambda execution role with minimal required permissions
- Security groups restricting ALB access to port 80
- API authentication via Secrets Manager

## Configuration

### Environment Variables
- `DEFAULT_MODEL`: anthropic.claude-3-sonnet-20240229-v1:0
- `ENABLE_CROSS_REGION_INFERENCE`: true
- `ENABLE_APPLICATION_INFERENCE_PROFILES`: true
- `ENABLE_PROMPT_CACHING`: configurable (false by default)

### IAM Permissions
The CloudFormation template creates the following IAM resources:

1. **ProxyApiHandlerServiceRole** (IAM Role)
- Allows the Lambda function to assume this role
- Attached with AWSLambdaBasicExecutionRole managed policy for CloudWatch Logs

2. **ProxyApiHandlerServiceRoleDefaultPolicy** (IAM Policy)
- Attached to the role above
- Grants permissions to:
- - `bedrock:ListFoundationModels` and `bedrock:ListInferenceProfiles` on all resources (*)
- - `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on Bedrock foundation models, inference profiles, and application inference profiles
- - `secretsmanager:GetSecretValue` and `secretsmanager:DescribeSecret` on the API key secret (specified by ApiKeySecretArn parameter)

3. **ProxyApiHandlerInvoke** (Lambda Permission)
- Allows the Application Load Balancer to invoke the Lambda function
- These IAM resources enable the Lambda function to:
- - Call Bedrock APIs to list and invoke models
- - Retrieve the API key from Secrets Manager for authentication
- - Write logs to CloudWatch
- - Be invoked by the ALB

## Architecture Benefits

The architecture follows AWS best practices with:
- Multi-AZ deployment for high availability
- Least-privilege IAM policies for security
- Secure credential management via Secrets Manager
- Serverless compute with Lambda for cost efficiency
- Load balancing for traffic distribution
