.POSIX:

default: namespace argocd root

namespace:
	kubectl create namespace argocd --dry-run=client --output=yaml \
		| kubectl apply -f -
	cd namespaces && helm template namespaces . | kubectl apply -f -

.PHONY: argocd
argocd: argocd/charts
	cd argocd && ./apply.sh

.PHONY: root
root:
	kubectl apply -f ./root/root-projects.yaml
	kubectl apply -f ./root/root.yaml
