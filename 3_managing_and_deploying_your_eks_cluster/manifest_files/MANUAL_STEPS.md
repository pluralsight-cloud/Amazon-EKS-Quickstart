# Manual Steps

---

## Creation

Here is each step listed out in the order of execution.
Use this file if following along, step by step.

> **NOTE**: Copy and pasting steps from here assume you are in this **local directory**!

1. Deploy EKS Cluster

```shell
eksctl create cluster -f ./1-cluster-config.yaml
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

10. Deploying TLS Version

Remember to first create your ACM TLS Cert, as well as the required Route 53 records for your ALB. Also, remember to remove the `dualstack.` from the Alias record name!

```shell
kubectl apply -f ./9-tls-ingress-config.yaml
```

---

## Cleaning Up

Here are the steps to clean up the resources if you need to!

1. Remove the existing manifest resources in reverse order

```shell
kubectl delete -f ./9-tls-ingress-config.yaml 2>/dev/null
kubectl delete -f ./8-ingress-config.yaml 2>/dev/null
kubectl delete -f ./7-ingressClass-config.yaml
kubectl delete -f ./6-service-config.yaml
kubectl delete -f ./5-deployment-config.yaml
```

2. Begin to delete the cluster

```shell
eksctl delete cluster -f ./1-cluster-config.yaml --force=true
```

3. Clean up any leftover resources (_Usually VPC_)

> Running twice to lazily double check deletion status

```shell
python3 python/clean_up.py
python3 python/clean_up.py
```

4. Delete cloudformation stack by force

```shell
aws cloudformation delete-stack --stack-name eksctl-test-cluster
```
