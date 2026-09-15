# Cluster benchmarks

These manifests are intentionally outside the Argo CD application roots. Run
them only when measuring a healthy cluster; the storage jobs generate 1 GiB of
I/O and kube-bench requires privileged host access.

```shell
kubectl apply -f test/benchmark/storage/rwo.yaml
kubectl apply -f test/benchmark/storage/rwx.yaml
kubectl apply -f test/benchmark/security/kube-bench.yaml

kubectl -n freshlab-benchmarks logs job/storage-rwo
kubectl -n freshlab-benchmarks logs job/storage-rwx
kubectl -n freshlab-security-benchmarks logs job/kube-bench
```

Delete the benchmark namespaces after collecting results.
