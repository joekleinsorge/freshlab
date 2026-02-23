.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)

default: metal system 

git-hooks:
	pre-commit install

metal:
	make -C metal $(if $(ANSIBLE_LIMIT),ANSIBLE_LIMIT='$(ANSIBLE_LIMIT)')

system:
	make -C system

clean:
	make -C metal teardown $(if $(ANSIBLE_LIMIT),ANSIBLE_LIMIT='$(ANSIBLE_LIMIT)')
