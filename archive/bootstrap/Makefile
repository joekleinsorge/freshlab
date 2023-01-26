.POSIX:
.EXPORT_ALL_VARIABLES:

default: namespace argocd root

argocd/charts: argocd/Chart.yaml
	cd argocd \
		&& helm dependency update

# TO-DO Make these namespaces into ArgoCD instead
namespace:
	kubectl create namespace argocd --dry-run=client --output=yaml \
		| kubectl apply -f -
	cd namespaces && helm template namespaces . | kubectl apply -f -

.PHONY: argocd
argocd: argocd/charts
	cd argocd && \
		./apply.sh

.PHONY: root
root:
	kubectl apply -f ./root/root-projects.yaml
	kubectl apply -f ./root/root-prod.yaml
