.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)
SOPS_AGE_KEY_FILE ?= $(CURDIR)/key.txt
DEX_SECRETS_FILE ?= freshlab-secrets/dex-secrets.sops.yaml
ARGOCD_OIDC_FILE ?= freshlab-secrets/argocd-oidc.sops.yaml
DEX_PASSWORD_FILE ?= /tmp/freshlab-dex-password.txt

default: help

git-hooks:
	pre-commit install

smoke-test:
	./scripts/cluster-smoke-test

backup-status:
	kubectl get replicationsources.volsync.backube -A \
		-o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,LAST:.status.lastSyncTime,NEXT:.status.nextSyncTime,RESULT:.status.latestMoverStatus.result'

restore:
	@test -n "$(NAMESPACE)" -a -n "$(SOURCE_PVC)" -a -n "$(RESTORE_PVC)" -a -n "$(CAPACITY)" || \
		{ echo 'Usage: make restore NAMESPACE=... SOURCE_PVC=... RESTORE_PVC=... CAPACITY=...'; exit 2; }
	argo submit --namespace argocd --from clusterworkflowtemplate/freshlab-volsync-restore \
		-p namespace="$(NAMESPACE)" -p source-pvc="$(SOURCE_PVC)" \
		-p restore-pvc="$(RESTORE_PVC)" -p capacity="$(CAPACITY)" --watch

paperless-password:
	@SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d --extract '["stringData"]["PAPERLESS_ADMIN_PASSWORD"]' freshlab-secrets/paperless.sops.yaml

new-app:
	@test -n "$(NAME)" -a -n "$(IMAGE)" -a -n "$(PORT)" -a -n "$(HOSTNAME)" || \
		{ echo 'Usage: make new-app NAME=... IMAGE=... PORT=... HOSTNAME=... [CONTAINER_PORT=...]'; exit 2; }
	./scripts/new-app "$(NAME)" "$(IMAGE)" "$(PORT)" "$(HOSTNAME)" $(if $(CONTAINER_PORT),"$(CONTAINER_PORT)")

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
		'  make smoke-test   Verify live nodes, Argo applications, and HTTPS routes' \
		'  make backup-status Show the latest and next VolSync backup runs' \
		'  make restore ...   Restore a backup into a new PVC' \
		'  make paperless-password Show the generated Paperless admin password' \
		'  make new-app ...   Scaffold a policy-aware Gateway API application' \
		'  make dex-password-hash  Show the configured Dex password hash' \
		'  make dex-password-reset Generate and save a new Dex password' \
		'  make argocd-auth-sync Apply Argo/Dex client secrets and restart SSO' \
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
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops --set '["stringData"]["DEX_ADMIN_PASSWORD_HASH"] "'"$$hash"'"' "$(DEX_SECRETS_FILE)" >/dev/null; \
	umask 077; printf '%s\n' "$$password" > "$(DEX_PASSWORD_FILE)"; \
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d "$(DEX_SECRETS_FILE)" | KUBECONFIG="$(KUBECONFIG)" kubectl apply -f - >/dev/null; \
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d "$(ARGOCD_OIDC_FILE)" | KUBECONFIG="$(KUBECONFIG)" kubectl apply -f - >/dev/null; \
	KUBECONFIG="$(KUBECONFIG)" kubectl -n dex rollout restart deployment/dex >/dev/null; \
	KUBECONFIG="$(KUBECONFIG)" kubectl -n argocd rollout restart deployment/argocd-server >/dev/null; \
	printf '%s\n' 'Dex password updated. Use this password with admin@kleinsorge.dev:'; \
	printf '%s\n' "$$password"; \
	printf '%s\n' "Password also saved to $(DEX_PASSWORD_FILE) (mode 600)."; \
	printf '%s\n' 'Dex is restarting; try the Argo CD login again in a few seconds.'

# Apply both sides of the Argo/Dex OIDC client configuration and restart them.
argocd-auth-sync:
	@set -e; \
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d "$(DEX_SECRETS_FILE)" | KUBECONFIG="$(KUBECONFIG)" kubectl apply -f - >/dev/null; \
	SOPS_AGE_KEY_FILE="$(SOPS_AGE_KEY_FILE)" sops -d "$(ARGOCD_OIDC_FILE)" | KUBECONFIG="$(KUBECONFIG)" kubectl apply -f - >/dev/null; \
	KUBECONFIG="$(KUBECONFIG)" kubectl -n dex rollout restart deployment/dex >/dev/null; \
	KUBECONFIG="$(KUBECONFIG)" kubectl -n argocd rollout restart deployment/argocd-server >/dev/null; \
	printf '%s\n' 'Argo/Dex SSO secrets applied; both services are restarting.'

# Print the bootstrap Argo CD local-admin password, if the bootstrap secret
# still exists. Normal access uses the Dex SSO login instead.
argocd-password:
	@KUBECONFIG="$(KUBECONFIG)" kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
