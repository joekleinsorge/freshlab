{
  description = "Freshlab development and operations environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in {
      devShells = forAllSystems (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          default = pkgs.mkShell {
            packages = with pkgs; [
              age
              ansible
              go
              jq
              kubeconform
              kubectl
              kubernetes-helm
              kustomize
              pre-commit
              shellcheck
              sops
              yamllint
              yq-go
            ];
            shellHook = ''
              export KUBECONFIG="$PWD/metal/kubeconfig.yaml"
              export SOPS_AGE_KEY_FILE="$PWD/key.txt"
              echo "Freshlab tools loaded. KUBECONFIG points at metal/kubeconfig.yaml."
            '';
          };
        });
    };
}
