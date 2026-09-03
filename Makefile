.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)
SOPS_AGE_KEY_FILE ?= $(CURDIR)/key.txt
DEX_SECRETS_FILE ?= $(CURDIR)/freshlab-secrets/dex-secrets.sops.yaml

default: help

git-hooks:
	pre-commit install

metal:
	make -C metal $(if $(ANSIBLE_LIMIT),ANSIBLE_LIMIT='$(ANSIBLE_LIMIT)')

system:
	make -C system

clean:
	make -C metal teardown $(if $(ANSIBLE_LIMIT),ANSIBLE_LIMIT='$(ANSIBLE_LIMIT)')

help:
	@printf '%s\n' \
		'Freshlab targets:' \
		'  make              Show this help' \
		'  make metal        Provision or manage the metal cluster' \
		'  make system       Deploy the system workloads' \
		'  make dex-password-hash  Show the configured Dex password hash' \
		'  make dex-password-reset Generate and save a new Dex password' \
		'  make argocd-password    Show the Argo CD local-admin password' \
		'  make clean        Tear down the metal cluster'

# Print the encrypted Dex admin password hash. Hashes cannot be used to log in
# directly; use this target to confirm which secret is configured.
dex-password-hash:
	@SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d --extract '["stringData"]["DEX_ADMIN_PASSWORD_HASH"]' "$(DEX_SECRETS_FILE)"

# Generate and save a new Dex admin password in the encrypted secret file.
dex-password-reset:
	@set -eu; \
	password=$$(openssl rand -hex 24); \
	hash=$$(htpasswd -bnBC 12 '' "$$password" | cut -d: -f2); \
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops --set '["stringData"]["DEX_ADMIN_PASSWORD_HASH"]' "\"$$hash\"" "$(DEX_SECRETS_FILE)" >/dev/null; \
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d "$(DEX_SECRETS_FILE)" | KUBECONFIG="$(KUBECONFIG)" kubectl apply -f - >/dev/null; \
	KUBECONFIG="$(KUBECONFIG)" kubectl -n dex rollout restart deployment/dex >/dev/null; \
	printf '%s\n' 'Dex password updated. Use this password with admin@kleinsorge.dev:'; \
	printf '%s\n' "$$password"; \
	printf '%s\n' 'Dex is restarting; try the Argo CD login again in a few seconds.'

# Print the bootstrap Argo CD local-admin password, if the bootstrap secret
# still exists. Normal access uses the Dex SSO login instead.
argocd-password:
	@KUBECONFIG="$(KUBECONFIG)" kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
