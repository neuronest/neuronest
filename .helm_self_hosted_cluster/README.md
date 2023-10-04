- See https://github.com/actions/actions-runner-controller
- See https://github.com/actions/actions-runner-controller/blob/master/docs/authenticating-to-the-github-api.md
- Create a GitHub App here for the organization: https://github.com/organizations/neuronest/settings/installations
  - define the APP_NAME (for example arc-neuronest)
  - store the APP_ID (on this page: https://github.com/organizations/neuronest/settings/apps/<APP_NAME>)
  - store the INSTALLATION_ID (viewable in the URL: https://github.com/organizations/neuronest/settings/installations/<INSTALLATION_ID>)
  - generate a private key here: https://github.com/organizations/neuronest/settings/apps/<APP_NAME> and download it

    
- run `source recreate_all.sh`

- see everything is running using `kubectl get pods -n arc-systems`

for example:

| NAME | READY | STATUS | RESTARTS | AGE |
| ------------- |:-------------:| -----:| -----:| -----:|
| arc-gha-rs-controller-6576fcfd54-xqw99 | 1/1 | Running | 0 | 2m21s |
| dind-deployment-7f48d794f5-mrdk7 | 1/1 | Running | 0 | 2m21s |
| neuronest-runner-set-6cd58d58-listener | 1/1 | Running | 0 | 2m10s |
| neuronest-runner-set-b6w4s-runner-8dhcb | 1/1 | Running | 0 | 2m8s |
| openebs-localpv-provisioner-658f7c597d-nwsmc | 1/1 | Running | 0 | 2m21s |
| openebs-ndm-288b4 | 1/1 | Running | 0 | 2m19s |
| openebs-ndm-operator-64fc5fc9c-bdszb | 1/1 | Running | 0 | 2m21s |
