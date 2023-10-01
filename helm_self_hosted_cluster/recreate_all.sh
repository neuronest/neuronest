current_directory="$(pwd)"

kind delete cluster --name kind

export NAMESPACE="arc-systems"
export APP_ID=388473
export INSTALLATION_ID=41691348
export PRIVATE_KEY_FILE_PATH="$current_directory/arc-neuronest.2023-09-11.private-key.pem"
export INSTALLATION_NAME="neuronest-runner-set"
export GITHUB_CONFIG_URL="https://github.com/neuronest/neuronest"

kind create cluster --config cluster.yaml
helm install arc \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller
kubectl create secret generic controller-manager \
    -n $NAMESPACE \
    --from-literal=github_app_id=${APP_ID} \
    --from-literal=github_app_installation_id=${INSTALLATION_ID} \
    --from-file=github_app_private_key=${PRIVATE_KEY_FILE_PATH}
helm install openebs openebs/openebs -n "${NAMESPACE}"
helm install "${INSTALLATION_NAME}" \
    --namespace "${NAMESPACE}" \
    -f runner.yaml \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set
for filename in dind_deployment.yaml dind_service.yaml docker_storage_pvc.yaml; do kubectl apply -f $filename; done
