#!/bin/bash
export AWS_PROFILE=think-tank
export AWS_REGION=eu-central-1
echo "Deploying to think-tank Account..."
aws sts get-caller-identity
agentcore deploy --agent astroAmber
