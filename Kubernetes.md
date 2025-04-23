

Disable swap (temporary, a permanent version is possible, but we'll do that later)

sudo swapoff -a

For Ubuntu, just use the 'Debian based' installation guide

https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/


sudo kubeadm init --pod-network-cidr=192.168.0.0/16


mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

make the filesystem shared for calico (need to verify if this is necessary):

sudo mount --make-shared /
findmnt -o TARGET,PROPAGATION /

https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart

On single node clusters, allow pods to be scheduled on the same node as the control plane:

kubectl taint nodes --all node-role.kubernetes.io/control-plane-



# Running the spec

Use podman

sudo apt install podman-docker

docker build -t docker-registry.default.svc.cluster.local:5000/upload_service:latest -f upload/Dockerfile upload

After building, save as tar file:

docker save -o upload_service.tar upload_service:latest

then, load into the ctr context:

sudo ctr -n k8s.io images import <path>/upload_service.tar

Security:

openssl genrsa -out ca.key 4096

openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=MyCA"

openssl genrsa -out registry.key 4096

openssl req -new -key registry.key -out registry.csr -config specs/openssl/registry.cnf

openssl x509 -req -in registry.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out registry.crt -days 365 -sha256 -extfile specs/openssl/registry.cnf -extensions req_ext

kubectl create secret tls registry-tls-secret \
    --cert=registry.crt \
    --key=registry.key

kubectl create configmap ca-cert --from-file=ca.crt



Use  this to find the image tag:

 sudo ctr -n k8s.io images list

 Update specs/upload-service-deployment.yaml to use the right tag

 We need to psuh the upload image to some image registry ideally.


kubectl apply -f specs/persistent-volume.yaml
kubectl apply -f specs/persistent-volume-claim.yaml
kubectl apply -f specs/registry-pv.yaml
kubectl apply -f specs/registry-deployment.yaml
kubectl apply -f specs/registry-nodeport-service.yaml
kubectl apply -f specs/registry-clusterip-service.yaml
kubectl apply -f specs/upload-service-deployment.yaml
kubectl apply -f specs/upload-service-service.yaml
kubectl apply -f specs/kaniko-job-role.yaml
kubectl apply -f specs/kaniko-job-rolebinding.yaml
kubectl apply -f specs/results-pv.yaml


kubectl get svc docker-registry -o jsonpath='{.spec.clusterIP}'

sudo vi /etc/hosts

10.98.158.28 docker-registry.default.svc.cluster.local


sudo cp ca.crt /etc/docker/certs.d/10.98.158.28:5000/ca.crt

if using podman:
sudo cp ca.crt /etc/containers/certs.d/10.98.158.28:5000/ca.crt

sudo mkdir -p /etc/containerd/certs.d/docker-registry.default.svc.cluster.local:5000
sudo cp ca.crt /etc/containerd/certs.d/docker-registry.default.svc.cluster.local:5000/ca.crt
sudo systemctl restart containerd

To test if it is working run:
curl -k https://docker-registry.default.svc.cluster.local:5000/v2/_catalog
This should return
{"repositories":[]}


kubectl run test-pod --rm -it --image=alpine -- /bin/sh
nslookup docker-registry.default.svc.cluster.local
exit

This is the same as the minikube service thing. This is called port forwarding, but I think a more sustainable option is to use a NodePort:

kubectl port-forward svc/upload-service 8080:80

zip -r example-job.zip example/

curl -X POST "http://127.0.0.1:8080/upload/" -F "file=@example-job.zip"




sudo mkdir -p /etc/containerd/certs.d/docker-registry.default.svc.cluster.local:5000
sudo cp /path/to/ca.crt /etc/containerd/certs.d/docker-registry.default.svc.cluster.local:5000/ca.crt

sudo vi /etc/containerd/config.toml


[plugins."io.containerd.grpc.v1.cri".registry]
  [plugins."io.containerd.grpc.v1.cri".registry.configs."docker-registry.default.svc.cluster.local:5000".tls]
    ca_file = "/etc/containerd/certs.d/docker-registry.default.svc.cluster.local:5000/ca.crt"
    insecure_skip_verify = false


sudo systemctl restart containerd


[plugins."io.containerd.grpc.v1.cri".registry]
  config_path = ""

  [plugins."io.containerd.grpc.v1.cri".registry.auths]

  [plugins."io.containerd.grpc.v1.cri".registry.configs]
    [plugins."io.containerd.grpc.v1.cri".registry.configs."docker-registry.default.svc.cluster.local:5000".tls]
      ca_file = "/etc/containerd/certs.d/docker-registry.default.svc.cluster.local:5000/ca.crt"
      insecure_skip_verify = false

  [plugins."io.containerd.grpc.v1.cri".registry.headers]

  [plugins."io.containerd.grpc.v1.cri".registry.mirrors]

[plugins."io.containerd.grpc.v1.cri".x509_key_pair_streaming]
  tls_cert_file = ""
  tls_key_file = ""


sudo systemctl restart containerd

https://chatgpt.com/share/67353270-0c64-800c-a091-0b62a4512724
