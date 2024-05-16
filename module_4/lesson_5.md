# Horizontally Autoscale Your Workload

This Markdown document contains the steps used during the Amazon EKS Quickstart horizontal scaling demo clip.

You must perform the following steps:

1. Deploy the Kubernetes Metrics Server (_URL provided_)
2. Deploy the Horizontal Pod Autoscaler sample application (_URL provided_)

---

## 1. Deploy a Default Amazon EKS Cluster

```shell
eksctl create cluster
```

## 2. Deploying the Metrics Server

This Metrics server Pod is required for the HPA to actually work. You should **NOT** use this for acutal metric
collection. It is only meant to be used for metric required to trigger Pod autoscaling.

Deploying the Metrics server Pods to an **EXISTING** EKS cluster:

```shell
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Checking the Deployment status:

```shell
kubectl get deployment metrics-server -n kube-system
```

## 3. Deploying the Sample Application

Deploy the simple Apache web server application provided in the documentation:

```shell
kubectl apply -f https://k8s.io/examples/application/php-apache.yaml
```

Create a Horizontal Pod Autoscaler resource with boundaries (_min_ and _max_ replicas):

```shell
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=5
```

Viewing the deployment and metrics:

```shell
kubectl get hpa
```

Deploying a load balancer for the web servers:

> Recommended to do this in a separate terminal tab/window so you can perform other actions in the meantime.

```shell
kubectl run -i \
    --tty load-generator \
    --rm --image=busybox \
    --restart=Never \
    -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://php-apache; done"
```

Viewing deployment and scaling activities:

> There will be a `5 minute` cooldown before the Pod scale down! This is default behavior.

```shell
kubectl get hpa php-apache --watch
```

## 4. Cleaning Up

To clean up the resources, you can run the following command:

```shell
eksctl delete cluster -n <name_of_your_cluster>
```

> NOTE: This will take several minutes.
