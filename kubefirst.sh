export GITHUB_TOKEN="$(cat ~/.secrets/gh-token)"
export CF_API_TOKEN="$(cat ~/.secrets/cf-api-token)"

kubefirst beta k3s create \
    --servers-args "--disable traefik,--write-kubeconfig-mode 0644" \
    --alerts-email lab@kleinsorge.dev \
    --dns-provider cloudflare \
    --domain-name kleinsorge.dev \
    --git-provider github \
    --github-org kleinsorge \
    --servers-private-ips 192.168.1.101, 192.168.1.102, 192.168.1.103 \
    --ssh-privatekey "$(cat ~/.ssh/id_ed25519)" \
    --ssh-user root \
    --cluster-name freshlab
