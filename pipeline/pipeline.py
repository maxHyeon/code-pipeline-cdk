from constructs import Construct
from aws_cdk import CfnOutput, Stack
from urllib.parse import urlparse
from aws_cdk import (
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_s3 as s3
)

import yaml


class DockerPipelineConstruct(Construct):

    def __init__(
        self, 
        scope: Construct, 
        id: str,
    ) -> None:
        super().__init__(scope=scope, id=id)
             
        name = scope.node.try_get_context("name")
        # ECR repositories
        container_repository = ecr.Repository(
            scope=self,
            id=f"{name}-container",
            repository_name=f"{name}"
        )
        # Repo for Application
        codecommit_repo = codecommit.Repository(
            scope=self, 
            id=f"{name}-container-git",
            repository_name=f"{name}-app",
            description=f"Application code"
        )
        # Repo for Helm
        codecommit_repo_helm = codecommit.Repository(
            scope=self, 
            id=f"{name}-helm-git",
            repository_name=f"{name}-helm",
            description=f"Helm Chart"
        )

        pipeline = codepipeline.Pipeline(
            scope=self, 
            id=f"{name}-container--pipeline",
            pipeline_name=f"{name}"
        )

        ssm_parameter = ssm.StringParameter(self, "mySsmParameter",
            parameter_name="/prod/codecommit-repo/e-mail",
            string_value="testuser@enablement-workshop.com"
        )

        # Outputs
        CfnOutput(
            scope=self,
            id="application_repository",
            value=codecommit_repo.repository_clone_url_http
        )
        source_output = codepipeline.Artifact()
        docker_output = codepipeline.Artifact(artifact_name="docker")
        helm_output = codepipeline.Artifact(artifact_name="helm")

        buildspec_docker = codebuild.BuildSpec.from_source_filename("buildspec.yml")

        with open('pipeline/helm_buildspec.yaml') as f:
            buildspec_yaml = yaml.load(f,Loader=yaml.FullLoader)
        buildspec_image_tag_push = codebuild.BuildSpec.from_object_to_yaml(buildspec_yaml)


        docker_build = codebuild.PipelineProject(
            scope=self,
            id=f"DockerBuild",
            environment=dict(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True),
            environment_variables={
                'REPO_ECR': codebuild.BuildEnvironmentVariable(
                    value=container_repository.repository_uri),
            },
            cache= codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
            build_spec=buildspec_docker
        )

        image_tag_push = codebuild.PipelineProject(
            scope=self,
            id=f"ImageTagPushToHelm",
            environment=dict(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                privileged=True),
            environment_variables={
                'HELM_REPO_URL' : codebuild.BuildEnvironmentVariable(
                    value=codecommit_repo_helm.repository_clone_url_http
                ),
                'REPO_ECR': codebuild.BuildEnvironmentVariable(
                    value=container_repository.repository_uri),
                'PROJ_NAME' : codebuild.BuildEnvironmentVariable(
                    value=f"{name}"
                )
            },
            build_spec=buildspec_image_tag_push
        )

        container_repository.grant_pull_push(docker_build)
        docker_build.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"],
            resources=[f"arn:{Stack.of(self).partition}:ecr:{Stack.of(self).region}:{Stack.of(self).account}:repository/*"],))

        image_tag_push.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ssm:GetParameters"],
            resources=[f"*"],))

        image_tag_push.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["codecommit:GitPull","codecommit:GitPush"],
            resources=[f"*"],))

        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit_Source",
            repository=codecommit_repo,
            output=source_output,
            branch="master"
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Stages in CodePipeline
        pipeline.add_stage(
            stage_name="DockerBuild",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name=f"DockerBuild_and_Push_ECR",
                    project=docker_build,
                    input=source_output,
                    outputs=[docker_output])
            ]
        )

        # Stages in Helm
        pipeline.add_stage(
            stage_name="Image_Tag_Push_To_Helm",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name=f"Image_Tag_Push_To_Helm",
                    project=image_tag_push,
                    input=docker_output,
                    outputs=[helm_output])
            ]
        )
