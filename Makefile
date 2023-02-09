.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)

default: metal bootstrap wait

git-hooks:
	pre-commit install

metal:
	make -C metal

bootstrap:
	make -C bootstrap

wait:
	python3 ./scripts/wait-main-apps

clean:
	make -C metal teardown
	./scripts/waitforssh metal1
