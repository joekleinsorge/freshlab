.POSIX:
.PHONY: *
.EXPORT_ALL_VARIABLES:

KUBECONFIG = $(shell pwd)/metal/kubeconfig.yaml
KUBE_CONFIG_PATH = $(KUBECONFIG)

default: metal bootstrap wait post-install

git-hooks:
	pre-commit install

metal:
	make -C metal

bootstrap:
	make -C bootstrap

wait:
	python3 ./scripts/wait-main-apps

post-install:
	python3 ./scripts/hacks

docs:
	docker run \
		--rm \
		--interactive \
		--tty \
		--publish 8000:8000 \
		--volume $(shell pwd):/docs \
		squidfunk/mkdocs-material

clean:
	make -C metal teardown
