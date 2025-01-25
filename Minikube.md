
START

minikube delete
minikube start

eval $(minikube -p minikube docker-env)

docker build -t upload_service:latest -f upload/Dockerfile upload


SECURITY (Do this first)

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


APPLY SPEC

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
kubectl apply -f specs/upload-service-job-role.yaml
kubectl apply -f specs/upload-service-rolebinding.yaml
kubectl apply -f specs/upload-service-sa.yaml

MAKE HOSTNAME RESOLVABLE BY NODES (Do this second)

Get the registry’s cluster IP
kubectl get svc docker-registry -o jsonpath='{.spec.clusterIP}'

Edit the /etc/hosts File manually
minikube ssh
sudo vi /etc/hosts

Add the following line to the etc/hosts file (this example assumes the cluster IP is 10.107.100.50)
10.107.100.50 docker-registry.default.svc.cluster.local

^^ Make sure to replace it with the cluster IP from the previous command

You should now be able to do the following in other pods like the test pod
kubectl run test-pod --rm -it --image=alpine -- /bin/sh
nslookup docker-registry.default.svc.cluster.local

exit


minikube cp ca.crt /home/docker/ca.crt

minikube ssh

sudo mkdir -p /etc/docker/certs.d/10.107.100.50:5000

sudo mv /home/docker/ca.crt /etc/docker/certs.d/10.107.100.50:5000/ca.crt

sudo systemctl restart docker

exit

Now in test pod you can
kubectl run test-pod --rm -it --image=alpine -- /bin/sh
apk add --no-cache curl
curl -k https://docker-registry.default.svc.cluster.local:5000/v2/_catalog



UPLOAD IMAGE

minikube service upload-service

zip -r example-job.zip example/

Get the URL and PORT from the minikube service command
curl -X POST "http://127.0.0.1:49949/upload/" \
     -F "file=@example-job.zip"


Add the ingress

minikube addons enable ingress
minikube tunnel

Check if its running
kubectl get pods -n ingress-nginx

Add the minikube ip as notebook.local (your domain)

Edit the /etc/hosts File manually
minikube ssh
sudo vi /etc/hosts

minikube ip

Add the following line to the etc/hosts file (this example assumes the minikube IP is 192.168.49.2)
192.168.49.2 notebooks.local *.notebooks.local

kubectl apply -f specs/service-creator-role.yaml
kubectl apply -f specs/service-creator-rolebinding.yaml
kubectl apply -f specs/upload-service-ingress-role.yaml
kubectl apply -f specs/upload-service-ingress-rolebinding.yaml

curl -X POST "http://127.0.0.1:49949/upload/" \
     -F "file=@example-job.zip"

curl -X POST "http://127.0.0.1:62141/ephemeral_notebook/" \
  -F "session_name=test-session1" \
  -F "image_name=jupyter/scipy-notebook:latest" \
  -F "ttl_seconds=6000" \
  -F "base_domain=notebooks.local"


Now, you need to add the returned subdomain to your host machines /etc/hosts/ example:
sudo nano /etc/hosts
add:
192.168.49.2 test-session1.notebooks.local

On supported systems you can just use a wildcard:
192.168.49.2 notebooks.local *.notebooks.local


This works on Safari, but not Chrome for now
