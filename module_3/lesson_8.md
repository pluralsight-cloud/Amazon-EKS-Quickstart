# Demo: Deploying Your Service Account and Cert Manager

The steps in this script will deploy our service account (SA) and some key components via deployments and services.
This is required to load balance our application via an Ingress (ALB).

```shell
kubectl apply -f .manifest_files/2-aws-load-balancer-controller-service-account.yaml
kubectl apply -f .manifest_files/3-cert-manager.yaml
kubectl wait --for=condition=available --timeout=120s deployment/cert-manager -n cert-manager
kubectl wait --for=condition=available --timeout=120s deployment/cert-manager-cainjector -n cert-manager
kubectl wait --for=condition=available --timeout=120s deployment/cert-manager-webhook -n cert-manager
python3 python/update_manifests.py
```