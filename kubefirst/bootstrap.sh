brew install konstructio/taps/kubefirst
brew install mkcert
mkcert -install
brew install nss
export GITHUB_TOKEN="$(cat  ~/git/local/secrets/gh)"
export CF_API_TOKEN=="$(cat  ~/git/local/secrets/cf)"

kubefirst k3s create \
    --servers-args "--disable traefik,--write-kubeconfig-mode 0644" \
    --alerts-email alerts.kleinsorge.dev \
    --dns-provider cloudflare \
    --domain-name kleinsorge.dev \
    --git-provider github \
    --github-org kleinsorge \
    --servers-private-ips 192.168.1.100,192.168.1.101,192.168.1.102 \
    --servers-public-ips 72.239.94.164, 72.239.94.164, 72.239.94.164 \
    --ssh-privatekey "$(cat  ~/.ssh/id_ed25519)" \
    --ssh-user root \
    --cluster-name homelab


export KUBECONFIG=~/.k1/kubeconfig


# Argo CD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Vault root token
kubectl -n vault get secret vault-unseal-secret -o jsonpath="{.data.root-token}" | base64 -d
