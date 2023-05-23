#!/bin/bash

initialize_terraform() {
  repository_name="$1"
  workspace="$2"
  bucket="$3"

  cd $repository_name/iac
  # run terraform init and create the terraform state locally
  terraform init -input=false -backend-config="bucket=$bucket"
  terraform workspace select $workspace || terraform workspace new $workspace
}
