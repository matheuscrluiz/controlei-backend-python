#!/bin/bash

IMAGE_REPO_NAME=$1
IMAGE_TAG=$2

echo "Scanning image..."
aws ecr start-image-scan --repository-name $IMAGE_REPO_NAME  --image-id imageTag=$IMAGE_TAG

echo "Waiting for completion of image scan..."
aws ecr wait image-scan-complete --repository-name $IMAGE_REPO_NAME --image-id imageTag=$IMAGE_TAG
echo "Image scan completed."

if [ $(echo $?) -eq 0 ]; then
  echo "Checking for high or critical vulnerabilities..."
  SCAN_FINDINGS=$(aws ecr describe-image-scan-findings --repository-name $IMAGE_REPO_NAME --image-id imageTag=$IMAGE_TAG | jq '.imageScanFindings.findingSeverityCounts')
  CRITICAL=$(echo $SCAN_FINDINGS | jq '.CRITICAL')
  HIGH=$(echo $SCAN_FINDINGS | jq '.HIGH')
  if [ "$CRITICAL" != null ] || [ "$HIGH" != null ]; then
    echo "Docker image contains vulnerabilities at CRITICAL or HIGH level"
    echo "Critical vulnerabilities: $CRITICAL"
    echo "High vulnerabilities: $HIGH"
    echo >> message.txt
    echo "Autor do commit: $CODEBUILD_GIT_AUTHOR" >> message.txt
    echo "Mensagem do commit: $CODEBUILD_GIT_MESSAGE" >> message.txt
    echo "Git Branch: $CODEBUILD_GIT_BRANCH" >> message.txt   
    echo "Check vulnerability report for $IMAGE_REPO_NAME:$IMAGE_TAG image in ECR repository"
    $CODEBUILD_BUILD_SUCCEEDING -eq 0
  else
    echo "Docker image is safe to be deploy"
  fi
fi