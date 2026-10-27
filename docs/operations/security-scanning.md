# Security scan gates

The supply-chain workflow scans the whole checkout for secrets and fixable
HIGH/CRITICAL dependency vulnerabilities. Those findings always fail the job.

The Kubernetes configuration scan retains its complete report, including existing
findings. Its deployment gate compares with the pull request's base revision, or
the previous revision for a push. Both revisions use the same installed Trivy
binary and policy database. There is no checked-in suppression list.

A configuration finding blocks the change if it is new, duplicated, identifies a
new resource, or occurs in a file whose bytes changed. An existing finding may be
reported without blocking only when its rule, message, occurrence count, path,
and the SHA256 of its source file match the baseline.
Vendored Helm templates use the digest of their owning chart archive, so a chart
upgrade cannot inherit its previous findings automatically.
Updating an insecure workload therefore requires fixing its findings first. Missing or malformed
reports and findings outside the checkout fail verification.

This separates existing configuration debt from new changes; it does not claim
that the retained findings are remediated. The `configuration-findings` artifact
contains both reports for review. Existing controller privileges and workload
hardening findings still need resource-specific investigation, including runtime
verification before changing privileges or making a filesystem read-only.
