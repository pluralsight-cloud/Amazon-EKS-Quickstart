REGION=us-east-1
SHELL := /bin/bash

1 install:	## Install
	$(info Creating Python virtual environment. Please ensure you activate the venv and install the requirements.)
	python3 -m venv python/venv
	. python/venv/bin/activate && pip install -r python/requirements.txt
	@printf "\nExecute the following command to leverage the Python venv: \tsource python/venv/bin/activate\n\n"

2 setup:	## Setup
	$(info Please set up AWS credential information in environment variables to use this Makefile...)
	@printf "Creating the cluster using the specified manifest file...\n"
	eksctl create cluster -f ./1-cluster-config.yaml
	@printf "\nCreating required IAM role and policy for AWS Load Balancer components...\n"
	@python3 python/create_eks_iam_role.py
	kubectl apply -f ./2-aws-load-balancer-controller-service-account.yaml
	kubectl apply -f ./3-cert-manager.yaml
	@printf "\nWaiting for cert-manager deployments to finish...\n"
	kubectl wait --for=condition=available --timeout=120s deployment/cert-manager -n cert-manager
	kubectl wait --for=condition=available --timeout=120s deployment/cert-manager-cainjector -n cert-manager
	kubectl wait --for=condition=available --timeout=120s deployment/cert-manager-webhook -n cert-manager
	@printf "\nUpdating the manifest files containing VPC ID information...\n"
	@python3 python/update_manifests.py

3 deploy:	## Deploy
	$(info Deploying application configs...)
	kubectl apply -f ./4-load-balancer-controller-config.yaml
	@printf "\nWaiting for ingress controller config to finish creating...\n"
	kubectl wait --for=condition=available --timeout=120s deployment/aws-load-balancer-controller -n kube-system
	kubectl apply -f ./5-deployment-config.yaml
	@printf "\nWaiting for app deployment to finish creating...\n"
	kubectl wait --for=condition=available --timeout=120s deployment/deployment-2048 -n game-2048
	kubectl apply -f ./6-service-config.yaml
	kubectl apply -f ./7-ingressClass-config.yaml
	kubectl apply -f ./8-ingress-config.yaml --validate=false
	@printf "\nPlease give the ALB a few minutes to deploy before testing.\n"

4 check:	## Check
	@printf "Checking ALB Ingress status...\n"
	kubectl get ingress/ingress-2048 -n game-2048

5 clean:	## Clean
	$(info Cleaning up existing resources that are no longer required...)
	$(info You are now deleting ALL cluster resources!)
	kubectl delete -f ./9-tls-ingress-config.yaml
	#kubectl delete -f ./8-ingress-config.yaml
	kubectl delete -f ./7-ingressClass-config.yaml
	kubectl delete -f ./6-service-config.yaml
	kubectl delete -f ./5-deployment-config.yaml
	eksctl delete cluster -f ./1-cluster-config.yaml --force=true
	@python3 python/clean_up.py
	@python3 python/clean_up.py
	@aws cloudformation delete-stack --stack-name eksctl-test-cluster
