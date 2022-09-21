k3sup install --host rocky01 --user root --cluster 
k3sup join --host rocky02 --server-ip 192.168.2.1 --user root --server
k3sup join --host rocky03 --server-ip 192.168.2.1 --user root --server