# Manual Steps

Here is each step listed out in the order of execution.
Use this file if following along, step by step.

> **NOTE**: Copy and pasting steps from here assume you are in this **local directory**!

1. Deploy EKS Cluster

```shell
eksctl create cluster -f ./1-cluster-config
```

2. Creating required IAM role and policy for AWS Load Balancer components

```shell
python3 ./python/create_eks_iam_role.py
kubectl apply -f ./2-aws-load-balancer-controller-service-account.yaml
```

3. Deploying cert-manager and then waiting for cert-manager deployments to finish

> NOTE: This is required for the aws-load-balancer component to create and manage our Ingress

```shell
kubectl apply -f ./3-cert-manager.yaml
kubectl wait --for=condition=available --timeout=120s deployment/cert-manager -n cert-manager
kubectl wait --for=condition=available --timeout=120s deployment/cert-manager-cainjector -n cert-manager
kubectl wait --for=condition=available --timeout=120s deployment/cert-manager-webhook -n cert-manager
```

4. Updating the manifest files containing our custom VPC ID information

```shell
python3 ./python/update_manifests.py
```

5. Deploying load balancer controller configs and waiting for the ingress controller config to finish creating

```shell
kubectl apply -f ./4-load-balancer-controller-config.yaml
kubectl wait --for=condition=available --timeout=120s deployment/aws-load-balancer-controller -n kube-system
```

6. Deploying deployment manifest and waiting

```shell
kubectl apply -f ./5-deployment-config.yaml
kubectl wait --for=condition=available --timeout=120s deployment/deployment-2048 -n game-2048
```

7. Deploying our game service

```shell
kubectl apply -f ./6-service-config.yaml
```

8. Deploying our Ingress Config and our Ingress (Please give the ALB a few minutes to deploy before testing)

```shell
kubectl apply -f ./7-ingressClass-config.yaml
kubectl apply -f ./8-ingress-config.yaml --validate=false
```

9. Checking Ingress status

```shell
kubectl get ingress/ingress-2048 -n game-2048
```
