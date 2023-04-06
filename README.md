# GitOps Homelab Project aka "Freshlab"

This is my GitOps homelab, or "Freshlab" because it's the latest version that I haven't burned down yet.

## Overview

This project is my homelab in a repo, utilizing some IaC and GitOps to manage the infrastructure and automate the provisioning, operating and updating of my self-hosted services.

Like every homelab, it's a work in progress, and I'm always looking for ways to improve it. If you have any suggestions, please feel free to open an issue or PR.

P.S. Don't rely on this for anything important, as it's not ready for production use.

## Features

- Re-deployment with a single command
- Automated k3s cluster provisioning and management
- GitOps managed cluster configuration
- Automatic rolling updates for OS and Kubernetes
- Automatic application updates
- Automatic TLS certificate provisioning and renewal
- Automatic DNS provisioning and management
- Automated monitoring configuration

## Core Components

I've broken the structure down into layers, each with their own purpose and function.

Main layers are structured in the following directories:

``` shell
.
├── metal     # L0.0 - Linux configuration and Kubernetes installation
├── bootstrap # L0.5 - GitOps bootstrap with ArgoCD Autopilot
├── system    # L1.0 - critical system components for the cluster
├── platform  # L2.0 - shared services for the apps components
├── apps      # L3.0 - user facing applications or services
├── global    # L4.0 - external or public-facing services
```


Supporting components:

``` shell
├── .github   # GitHub Actions workflows for CI
├── scripts   # Supporting scripts for managing the cluster
└── docs      # Documentation lives here```
```

## Documentation

See the docs for detailed information on the architecture, installation and use of the platform.

## Acknowledgements

This design was heavily inspired by the following projects:

- [K8s-at-home](https://github.com/k8s-at-home)
- [Khuedon's homelab](https://github.com/khuedoan/homelab)
- [Locmai's humble](https://github.com/locmai/humble)