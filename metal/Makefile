.POSIX:

default: cluster

cluster:
	ansible-playbook \
		--inventory inventories/prod.yml \
		cluster.yml
	cp $(shell pwd)/metal/kubeconfig.yaml ~/.kube/config

console:
	ansible-console \
		--inventory inventories/prod.yml

teardown:
	ansible-playbook \
		--inventory inventories/prod.yml \
		teardown.yml