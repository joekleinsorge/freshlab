# Commands  

```bash


# Traefik
k create ns traefik
helm repo add traefik https://helm.traefik.io/traefik
helm install traefik traefik/traefik -f traefik/values.yaml -n traefik
k get svc --all-namespaces -o wide

```
