# Steps

## Create

```shell
make metal 
# or
k create namespace cert-manager
k apply -f global/cert-manager/secret.yaml
helm install cert-manager jetstack/cert-manager -f global/cert-manager/values.yaml -n cert-manager
k create namespace metallb-system
k apply -f metal/roles/metallb_config/files/configmap.yaml   
k apply -f metal/roles/metallb_config/files/ipaddresspool.yaml
helm install metallb metallb/metallb -f system/metallb-system/values.yaml -n metallb-system
k create namespace ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --values system/ingress-nginx/values.yaml
kubectl -n ingress-nginx get all
```

## teardown

``` shell
helm delete metallb metallb/metallb -n metallb-system
helm delete ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx 
```
