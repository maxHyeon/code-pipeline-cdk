## EKS Enablement - CICD Workshop 환경 배포를 위한 CDK
### based on 
https://github.com/aws-samples/aws-cdk-eks-flux
#### Requirements
  - CDK installed: [Getting started with the AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html)
  - AWS Account
  - IAM user with Git Credentials for Codecommit: [IAM Git Credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_ssh-keys.html)

###  Steps to reproduce

cdk.json 에서 세부 설정 변경

```
{
  "app": "python3 app.py",
  "context": {
    "aws-cdk:enableDiffNoFail": "true",
    "@aws-cdk/core:stackRelativeExports": "true",
    "@aws-cdk/aws-ecr-assets:dockerIgnoreSupport": true,
    "name": "Project name",
    "region": "Region"
  }
}
```

Deploy the infrastructure using the CDK cli:

```
cdk bootstrap aws://account_id/us-east-1
cdk deploy
```

Docker Build 단계
- Docker Build 를 진행한 뒤 ECR로 배포

Image Tag Push 단계
- ECR 로 Push 된 Image 의 TAG 정보를 helm chart 의 values.yaml 에 업데이트 하여 helm chart codecommit repo로 push
- 최종적으로 Argo CD에서 Helm Repo Syne를 맞춤


###  Clean up
After completing your demo, delete your stack using the CDK cli:
```
cdk destroy
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.