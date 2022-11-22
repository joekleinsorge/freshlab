# Setup

## Cluster components

- [metallb](https://metallb.universe.tf/): For internal cluster networking using BGP.
- [longhorn](https://longhorn.io): Provides persistent volumes, allowing any application to consume block storage.
- [cert-manager](https://cert-manager.io/docs/): Configured to create TLS certs for all ingress services automatically using LetsEncrypt.
- [ingress-nginx](https://kubernetes.github.io/ingress-nginx/): My preferred ingress controller to expose traffic to pods over DNS.
- [vault](https://www.vaultproject.io/): Hashicorp Vault to Manage Secrets & Protect Sensitive Data and internal self-signed TLS certs

## Automate all the things

- [Github Actions](https://docs.github.com/en/actions) for checking code formatting
- Rancher [System Upgrade Controller](https://github.com/rancher/system-upgrade-controller) to apply updates to k3s
- [Renovate](https://github.com/renovatebot/renovate) with the help of the [k8s-at-home/renovate-helm-releases](https://github.com/k8s-at-home/renovate-helm-releases) Github action keeps my application charts and container images up-to-date

## Tools

| Tool                                                   | Purpose                                                   |
|--------------------------------------------------------|-----------------------------------------------------------|
| [k9s](https://github.com/derailed/k9s)                 | Kubernetes CLI To Manage Your Cluster                     |
| [pre-commit](https://github.com/pre-commit/pre-commit) | Enforce code consistency and verifies no secrets are pushed |
| [stern](https://github.com/stern/stern)                | Tail logs in Kubernetes                                   |
