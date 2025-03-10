.POSIX:

default: cluster

cluster:
	ansible-playbook \
		--inventory inventory.ini \
		cluster.yml
	cp $(shell pwd)/kubeconfig.yaml ~/.kube/config

console:
	ansible-console \
		--inventory inventory.ini

