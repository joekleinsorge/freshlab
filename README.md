# Freshlab: My GitOps Homelab Project

This is my GitOps homelab, or "Freshlab" because it's the latest version that I haven't burned down yet.

## Overview

This project is my homelab in a repo, utilizing some IaC and GitOps to manage the infrastructure and automate the provisioning, operating and updating of my self-hosted services.

Please note that Freshlab is a personal project and not intended for production use. It's a continuously evolving work-in-progress, and feedback, suggestions, and contributions from the community are welcome to further enhance its capabilities.

## Features

- One-command re-deployment for seamless updates
- Automated k3s cluster provisioning and management for efficient operations
- GitOps managed cluster configuration for declarative and version-controlled infrastructure management
- Automatic rolling updates for the operating system and Kubernetes for improved security and stability
- Automatic application updates for self-hosted services, ensuring the latest features and bug fixes
- Automatic TLS certificate provisioning and renewal for secure communication over HTTPS
- Automatic DNS provisioning and management for easy domain configuration
- Automated monitoring configuration for enhanced observability and insights into the environment

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
└── docs      # Documentation lives here
```

## Documentation

See the docs for detailed information on the architecture, installation and use of the platform.

## Acknowledgements

This design was inspired by the following projects:

- [K8s-at-home](https://github.com/k8s-at-home)
- [Khuedon's homelab](https://github.com/khuedoan/homelab)
- [Locmai's humble](https://github.com/locmai/humble)