.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)

default: metal system 

git-hooks:
	pre-commit install

metal:
	make -C metal

system:
	make -C system

clean:
	make -C metal teardown
	./scripts/waitforssh metal1
