.POSIX:

GIT_REPO=https://github.com/joekleinsorge/freshlab
GIT_TOKEN=$(shell cat .token)

bootstrap:
	argocd-autopilot repo bootstrap --recover \
		--git-token=$(GIT_TOKEN) \
		--repo=$(GIT_REPO) \
		--app "${GIT_REPO}.git/bootstrap/argo-cd"
