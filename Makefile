.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)

default: metal git-hooks

git-hooks:
	pre-commit install

metal:
	make -C metal

clean:
	make -C metal teardown
	./scripts/waitforssh metal1
