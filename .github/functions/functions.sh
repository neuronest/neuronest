#!/bin/bash

initialize_terraform() {
  workspace="$1"
  bucket="$2"

  # run terraform init and create the terraform state locally
  terraform init -input=false -backend-config="bucket=$bucket"
  terraform workspace select $workspace || terraform workspace new $workspace
}