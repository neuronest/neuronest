#!/bin/bash

install_terraform() {
  export DEBIAN_FRONTEND=noninteractive
  apt -qqy update > /dev/null && apt-get install -qqy gnupg software-properties-common zip unzip wget > /dev/null
  wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
  gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint
  echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
  apt -qqy update > /dev/null
  apt install -qqy terraform > /dev/null
}
