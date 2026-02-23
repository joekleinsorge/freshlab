.POSIX:

default: cluster

ANSIBLE_INVENTORY ?= inventories/prod.yml
ANSIBLE_LIMIT ?=
CLUSTER_ALLOW_UNREACHABLE ?= true
CLUSTER_RUN_PREFLIGHT ?= true
TEARDOWN_ALLOW_UNREACHABLE ?= true
KUBECONFIG_FILE ?= $(HOME)/.kube/config
KUBECONFIG_CONTEXT ?= freshlab

preflight:
	ansible-playbook \
		--inventory $(ANSIBLE_INVENTORY) \
		$(if $(ANSIBLE_LIMIT),--limit $(ANSIBLE_LIMIT)) \
		preflight.yml

cluster:
	@set -e; \
	if [ "$(CLUSTER_RUN_PREFLIGHT)" = "true" ]; then \
		$(MAKE) preflight ANSIBLE_INVENTORY="$(ANSIBLE_INVENTORY)" ANSIBLE_LIMIT="$(ANSIBLE_LIMIT)"; \
	fi; \
	rc=0; \
	ansible-playbook \
		--inventory $(ANSIBLE_INVENTORY) \
		$(if $(ANSIBLE_LIMIT),--limit $(ANSIBLE_LIMIT)) \
		cluster.yml || rc=$$?; \
	if [ "$$rc" -eq 4 ] && [ "$(CLUSTER_ALLOW_UNREACHABLE)" = "true" ]; then \
		echo "cluster: unreachable hosts detected (exit code 4), treating as non-fatal"; \
		rc=0; \
	fi; \
	if [ "$$rc" -eq 0 ]; then \
		if [ ! -f "$(shell pwd)/kubeconfig.yaml" ]; then \
			echo "cluster: kubeconfig.yaml not found, skipping kubeconfig import"; \
		elif ! command -v kubectl >/dev/null 2>&1; then \
			echo "cluster: kubectl not found, skipping kubeconfig import"; \
		else \
			mkdir -p "$$(dirname "$(KUBECONFIG_FILE)")"; \
			tmp_cluster=$$(mktemp); \
			tmp_merged=$$(mktemp); \
			awk -v ctx="$(KUBECONFIG_CONTEXT)" '\
				/^[[:space:]]*(-[[:space:]]*)?name:[[:space:]]*default[[:space:]]*$$/ { sub(/name:[[:space:]]*default[[:space:]]*$$/, "name: " ctx) } \
				/^[[:space:]]*cluster:[[:space:]]*default[[:space:]]*$$/ { sub(/default[[:space:]]*$$/, ctx) } \
				/^[[:space:]]*user:[[:space:]]*default[[:space:]]*$$/ { sub(/default[[:space:]]*$$/, ctx) } \
				/^current-context:[[:space:]]*default[[:space:]]*$$/ { sub(/default[[:space:]]*$$/, ctx) } \
				{ print }\
			' "$(shell pwd)/kubeconfig.yaml" > "$$tmp_cluster"; \
			if [ -f "$(KUBECONFIG_FILE)" ]; then \
				KUBECONFIG="$(KUBECONFIG_FILE):$$tmp_cluster" kubectl config view --flatten > "$$tmp_merged"; \
			else \
				KUBECONFIG="$$tmp_cluster" kubectl config view --flatten > "$$tmp_merged"; \
			fi; \
			mv "$$tmp_merged" "$(KUBECONFIG_FILE)"; \
			chmod 600 "$(KUBECONFIG_FILE)"; \
			kubectl config --kubeconfig "$(KUBECONFIG_FILE)" use-context "$(KUBECONFIG_CONTEXT)" >/dev/null 2>&1 || true; \
			rm -f "$$tmp_cluster"; \
		fi; \
	fi; \
	exit $$rc

console:
	ansible-console \
		--inventory $(ANSIBLE_INVENTORY) \
		$(if $(ANSIBLE_LIMIT),--limit $(ANSIBLE_LIMIT))

teardown:
	@set -e; \
	rc=0; \
	ansible-playbook \
		--inventory $(ANSIBLE_INVENTORY) \
		$(if $(ANSIBLE_LIMIT),--limit $(ANSIBLE_LIMIT)) \
		teardown.yml || rc=$$?; \
	if [ "$$rc" -eq 4 ] && [ "$(TEARDOWN_ALLOW_UNREACHABLE)" = "true" ]; then \
		echo "teardown: unreachable hosts detected (exit code 4), treating as non-fatal"; \
		exit 0; \
	fi; \
	exit $$rc
