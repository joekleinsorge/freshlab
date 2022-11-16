# Freshlab


> **Warning**
> This is a WIP

Sometime you just have to start fresh.  

```shell
┌───────────────────────────┐
│      L3. Applications     ◄──────────────────┐
└─────────────▲─────────────┘                  |
              │                                |
┌─────────────┴─────────────┐                  |
│       L2. Platform        ◄──────────────────┤
└─────────────▲─────────────┘                  │
              │                                │
┌─────────────┴─────────────┐                  │
│        L1. System         |                  |
└─────────────▲─────────────┘                  │
              │                                │
┌─────────────┴─────────────┐   ┌──────────────┴────────────┐
│        L0. Metal          ◄───┤     LE. Third-parties     │
└───────────────────────────┘   └───────────────────────────┘
```

Main layers are structured in the following directories:
    - ./metal: bare metal management, install Linux and Kubernetes.
    - ./bootstrap: GitOps bootstrap with ArgoCD.
    - ./system: critical system components for the cluster (load balancer, storage, ingress, -operation tools...).
    - ./platform: shared services for the apps components to utilize on.
    - ./apps: user facing applications or services/
    - ./global (optional): public-facing managed services including the Cloudflare provisioning and DNS setup.

Support components:
    - ./tools: tools container, includes all the tools and scripts you'll need for operations.
    - ./docs: all documentation go here, this will generate a searchable web UI.


Run `make` and:
    (1) Build the ./metal layer:
        Install Linux on all servers in parallel
        Build a Kubernetes cluster (based on k3s)
    (2) Build the ./bootstrap layer:
        Install ArgoCD
        Configure the root app to manage other layers (and also manage itself)

From then on, ArgoCD will do the rest:

    (3) Build the ./system layer (storage, networking, monitoring, etc)
    (4) Build the ./platform layer (Gitea, Vault, etc)
    (5) Build the ./apps layer: (Dashy, Yuta, Dendrite, etc)
    (6) Build the ./global layer: (Cloudflare and stuffs)
