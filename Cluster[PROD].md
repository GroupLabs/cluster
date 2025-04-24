Build the upload service image:

```
podman build -t upload_service:latest .

sudo podman tag localhost/upload_service:latest upload_service:latest

sudo podman save -o upload_service.tar upload_service:latest

sudo podman load -i upload_service.tar

# verify
sudo crictl images | grep upload_service
```

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

Clean up artifacts:

rm upload_service.tar
