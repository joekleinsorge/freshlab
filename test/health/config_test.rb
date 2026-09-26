require "yaml"
require "open3"

def render(path)
  output, status = Open3.capture2("helm", "template", File.basename(path), path, "-n", File.basename(path))
  raise "Render failed: #{path}" unless status.success?
  YAML.load_stream(output).compact
end

def check(condition, message)
  raise message unless condition
end

routes = render("system/istio-system")
values = YAML.load_file("system/istio-system/values.yaml")
bootstrap_namespaces = YAML.load_stream(File.read("freshlab-secrets/namespaces.yaml")).compact
gateway = routes.find { |d| d["kind"] == "Gateway" && d.dig("metadata", "name") == "freshlab" }
check(gateway, "Shared public Gateway is missing")
check(gateway.dig("metadata", "annotations", "external-dns.kubernetes.io/target") == values["publicGatewayAddress"],
      "Shared Gateway DNS target must match publicGatewayAddress")
check(gateway.dig("spec", "infrastructure", "parametersRef") == {
        "group" => "", "kind" => "ConfigMap", "name" => "freshlab-gateway-infrastructure"
      }, "Shared Gateway must reference its scheduling overlay")
gateway_infrastructure = routes.find { |d| d["kind"] == "ConfigMap" && d.dig("metadata", "name") == "freshlab-gateway-infrastructure" }
check(gateway_infrastructure, "Shared Gateway scheduling overlay is missing")
gateway_deployment = YAML.safe_load(gateway_infrastructure.dig("data", "deployment"))
check(gateway_deployment.dig("spec", "replicas") == 2,
      "Shared Gateway must keep two replicas for node and rollout availability")
check(gateway_deployment.dig("spec", "template", "spec", "priorityClassName") == "freshlab-public-gateway",
      "Shared Gateway must retain its dedicated priority class")
gateway_toleration = gateway_deployment.dig("spec", "template", "spec", "tolerations")&.find do |toleration|
  toleration == {
    "key" => "freshlab.io/network-speed", "operator" => "Equal", "value" => "100m", "effect" => "NoSchedule"
  }
end
check(gateway_toleration, "Shared Gateway must tolerate the low-bandwidth node during capacity pressure")
gateway_anti_affinity = gateway_deployment.dig("spec", "template", "spec", "affinity", "podAntiAffinity", "requiredDuringSchedulingIgnoredDuringExecution")
check(gateway_anti_affinity&.any? { |term|
  term["topologyKey"] == "kubernetes.io/hostname" &&
    term.dig("labelSelector", "matchLabels", "gateway.networking.k8s.io/gateway-name") == "freshlab"
}, "Shared Gateway replicas must be placed on separate nodes")
gateway_pdb = routes.find { |d| d["kind"] == "PodDisruptionBudget" && d.dig("metadata", "name") == "freshlab-public-gateway" }
check(gateway_pdb&.dig("spec", "minAvailable") == 1,
      "Shared Gateway must retain one replica during voluntary disruption")
values.fetch("appRoutes").each do |route|
  namespace = routes.find { |d| d["kind"] == "Namespace" && d["metadata"]["name"] == route["namespace"] }
  check(namespace, "Missing namespace management: #{route['namespace']}")
  expected = values["privilegedNamespaces"].include?(route["namespace"]) ? "privileged" : "baseline"
  check(namespace["metadata"]["labels"]["pod-security.kubernetes.io/enforce"] == expected,
        "Incorrect admission policy: #{route['namespace']}")
  bootstrap = bootstrap_namespaces.find { |d| d["metadata"]["name"] == route["namespace"] }
  if bootstrap
    (bootstrap["metadata"]["labels"] || {}).each do |key, value|
      desired = namespace["metadata"]["labels"][key]
      check(desired.nil? || desired == value, "Conflicting namespace owners: #{route['namespace']}/#{key}")
    end
  end
  if route["protected"]
    check(!routes.any? { |d| d["kind"] == "HTTPRoute" && d["metadata"]["namespace"] == route["namespace"] },
          "Protected app has a route bypassing authentication")
  end
end

argo = render("system/argocd")
appsets = argo.select { |d| d["kind"] == "ApplicationSet" }
check(!appsets.empty?, "No ApplicationSets rendered")
appsets.each do |appset|
  ignores = appset.dig("spec", "template", "spec", "ignoreDifferences") || []
  ignores.select { |r| r["kind"] == "Namespace" }.each do |rule|
    check(!(rule["jqPathExpressions"] || []).include?(".metadata.labels"),
          "Argo must reconcile namespace security and mesh labels")
  end
end
executor = argo.find { |d| d["kind"] == "Role" && d["metadata"]["name"] == "freshlab-workflow-executor" }
check(executor && executor["rules"] == [{"apiGroups"=>["argoproj.io"], "resources"=>["workflowtaskresults"], "verbs"=>["create", "patch"]}],
      "Workflow executor must have only namespace-scoped result permissions")
config = argo.find { |d| d["kind"] == "ConfigMap" && d["metadata"]["name"].end_with?("workflow-controller-configmap") }
check(YAML.safe_load(config["data"]["config"]).dig("workflowDefaults", "spec", "serviceAccountName") == "freshlab-workflow-executor",
      "Workflows without an explicit account need the executor default")

%w[apps/hajimari apps/kube-ops-view apps/librespeed apps/uptime-kuma platform/dex platform/grafana apps/frigate].each do |path|
  check(render(path).none? { |d| d["kind"] == "Ingress" }, "#{path} reintroduces obsolete Ingress")
end
%w[apps/budget apps/excalidraw apps/flask apps/grocy apps/kitchenowl apps/mealie apps/tools platform/authelia].each do |path|
  Dir.glob("#{path}/*.yaml").each do |file|
    check(YAML.load_stream(File.read(file)).compact.none? { |d| d["kind"] == "Ingress" }, "#{file} reintroduces obsolete Ingress")
  end
end
puts "Health configuration regression checks passed."
