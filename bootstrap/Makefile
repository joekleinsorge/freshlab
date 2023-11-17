.POSIX:

GIT_REPO=https://github.com/joekleinsorge/freshlab
GIT_TOKEN=$(shell cat .token)

default: argocd root

argocd:
	argocd-autopilot repo bootstrap --recover \
		--git-token=$(GIT_TOKEN) \
		--repo=$(GIT_REPO) \
		--app "${GIT_REPO}.git/bootstrap/argo-cd"

root:
	cd root && ./apply.sh
