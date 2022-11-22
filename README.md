# Freshlab

> **Warning**
> This is a WIP

Sometime you just have to start fresh.  

```shell
┌───────────────────────────┐   ┌──────────────────────────┐
│      L3. Applications     ◄───┤       L4. Global         │
└─────────────▲─────────────┘   └──────────────────────────┘               
              │                                |
┌─────────────┴─────────────┐                  |
│       L2. Platform        ◄──────────────────┘
└─────────────▲─────────────┘                  
              │                                
┌─────────────┴─────────────┐                  
│        L1. System         |                 
└─────────────▲─────────────┘                 
              │                                
┌─────────────┴─────────────┐
│        L0. Metal          │
└───────────────────────────┘
```

Main layers are structured in the following directories:
    - (L0.0) ./metal: bare metal management, installs Linux and Kubernetes
    - (L0.5) ./bootstrap: GitOps bootstrap with ArgoCD
    - (L1.0) ./system: critical system components for the cluster (load balancer, storage, ingress, -operation tools...)
    - (L2.0) ./platform: shared services for the apps components to utilize
    - (L3.0) ./apps: user facing applications or services
    - (L4.0) ./global: public-facing managed services including the Cloudflare provisioning and DNS setup

Support components:
    - ./tools: tools container, includes all the tools and scripts you'll need for operations.
    - ./docs: all documentation go here, this will generate a searchable web UI.
