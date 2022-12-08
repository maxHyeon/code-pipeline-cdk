#!/usr/bin/env python3

from aws_cdk import App, Environment, Stack
from pipeline.pipeline import DockerPipelineConstruct
import os

app = App()

name = app.node.try_get_context("name")
region = app.node.try_get_context("region")

aws_env = Environment(region=region)
stack = Stack(scope=app,id=f"{name}-stack",env=aws_env)

eks_enablement_pipeline = DockerPipelineConstruct(
    scope=stack,
    id=f"{name}-docker-pipeline"
)

app.synth()
