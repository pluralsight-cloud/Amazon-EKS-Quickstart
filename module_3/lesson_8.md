# Demo: Deploying our Application and Service

This set of scripted steps deploys our application, as well as our Ingress!

```shell
kubectl apply -f .manifest_files/4-load-balancer-controller-config.yaml
kubectl wait --for=condition=available --timeout=120s deployment/aws-load-balancer-controller -n kube-system
kubectl apply -f ./5-deployment-config.yaml
kubectl wait --for=condition=available --timeout=120s deployment/deployment-2048 -n game-2048
kubectl apply -f ./6-service-config.yaml
kubectl apply -f ./7-ingressClass-config.yaml
kubectl apply -f ./8-ingress-config.yaml --validate=false
```