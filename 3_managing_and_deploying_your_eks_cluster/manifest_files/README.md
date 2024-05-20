# Deploying our ALB Fronted Sample Application

## Makefile

We have provided a Makefile for you to leverage if desired.
This Makefile provides all of the required steps for deploying your application to Amazon EKS successfully.

### Steps

Below we will walk through each step of the process and provide an overview of what the step completes each time.
The steps are listed in the order you should execute them.

**You can reference the targets by name, or by numbered step! Both solutions are provided.**

#### 1. install

```shell
make install
```

OR

```shell
make 1
```

During this `install` step of the Make process, you will create a new Python virtual environment to source and use.
You will see two additional commands output for you to copy and paste, including activating the new venv, and installing
the required packages via pip.

#### 2. setup

```shell
make setup
```

OR

```shell
make 2
```

The `setup` step will go through and perform several functions.

1. It will create a brand new Amazon EKS cluster named **test** in the **us-east-1** Region using mostly default
   settings. It will
   reference the **1-cluster-config.yaml** file to create the cluster. Your cluster will be split within a brand new VPC
   that will have networking resources deploy to 2 different Availability Zones. In addition, it will deploy new Fargate
   profiles, as well as several new IAM service accounts and cluster add-ons.
2. It will execute a custom Python script to generate a second yaml manifest file that contains the service account
   information for the required AWS Load Balancer Controller Service Account.
3. After creation of the manifest above (**2-aws-load-balancer-controller-service-account.yaml**), you deploy it
   via `kubectl`.
4. Next, you deploy the required **3-cert-manager.yaml** to deploy several key resources within your cluster that are
   needed for creating a new Ingress controller.
5. We have added several wait conditions to wait for the components from that manifest to be ready, and then it will
   move on to running another custom Python script that updates an existing template with the required information and
   then outputs the **4-load-balancer-controller-config.yaml** file.

#### 3. deploy

```shell
make deploy
```

OR

```shell
make 3
```

This `deploy` step will now work on deploying the rest of the application and the ingress controller.

1. You apply the newly created **4-load-balancer-controller-config.yaml** manifest file to create the load balancer
   controller pods.
2. We implement another wait condition for this to complete, and then once ready, we actually deploy our 2048 game
   application pods.
3. After those are deployed and verified to be ready via another wait, you then deploy the **6-service-config.yaml**
   manifest to create the Service that references the new deployments.
4. Next, you deploy a new IngressClass configuration via the **7-ingressClass-config.yaml** manifest file.
5. The Ingress Class config is used when we deploy the **8-ingress-config.yaml** manifest immediately after. This
   Ingress (_ALB_) references the Service that we deployed in the previous steps as the backend.

#### 4. check

```shell
make check
```

OR

```shell
make 4
```

Running this step allows you to check the progress and status of your ALB that was created. You will see an example
output like this:

```text
NAME           CLASS   HOSTS   ADDRESS                                                                  PORTS   AGE
ingress-2048   alb     *       k8s-game2048-ingress2-0d50dcef8e-784051621.us-east-1.elb.amazonaws.com   80      10s
```

You can then test status by navigating to the provided ALB address in the output! **Make sure you navigate to port 80
only (HTTP)!**

#### dns and tls

Now we can test creating a new Route53 DNS Record to reference our application ALB. Then, we will implement a TLS
certificate and redirect HTTP to HTTPS!

##### Create DNS Record

1. Navigate to Route 53
1. Find and select your Sandbox Public Hosted Zone (Example: `677538000670.realhandsonlabs.net`)
1. Click on `Create record`
2. Set the **Record type** to an `A` record
1. Give your record a name of your choosing (Example: `app.677538000670.realhandsonlabs.net`)
2. Toggle on the `Alias` toggle button
3. Under **Route traffic to** select `Alias to Application and Classic Load Balancer`, then `us-east-1` for the Region
4. Search and find your newly created Ingress ALB from the dropdown
5. **IMPORTANT!** Remove the `dualstack.` from the beginning of your ALB selected. This is a bug in the console!
6. Leave everything else the same and click `Create records`
7. Test navigating to your HTTP DNS record (Example: `http://app.677538000670.realhandsonlabs.net`)

##### Create TLS

With public DNS working, let's implement TLS!

1. Navigate to AWS Certificate Manager
2. Click on `Request a certificate`
3. For **Certificate type** select `Request a public certificate` and click `Next`
4. Enter your same DNS name as the previous steps. (Example: `app.677538000670.realhandsonlabs.net`)
5. Under **Validation method** select `DNS validation - recommended`
6. Leave the rest as default values and click on `Request`
7. Once your certificate is visible, it should say _Pending validation_. Select it and navigate to the **Domains**
   section.
8. Find and select `Create records in Route 53`, then `Create records` on the next page
9. Once you get a successful message, navigate to your Route 53 Public Hosted Zone and verify the record exists
10. Once verified the record exists, go back to ACM and refresh the page with the cert listed.
11. It should change to _Issued_ fairly quickly.

#### (Optional) Implement Ingress TLS

1. You should now see a `9-tls-ingress-config.yaml` manifest file in your directory
2. Run the following command to set up TLS and HTTP redirects:

```shell
kubectl apply -f 9-tls-ingress-config.yaml
```

3. This will eventually implement TLS for your recently created Ingress! Congrats!
4. Test via HTTPS (Example: `https://app.677538000670.realhandsonlabs.net`)

#### 5. clean

```shell
make clean
```

OR

```shell
make 5
```

This step goes through and force deletes ALL resources associated with your newly deployed EKS cluster.
