# kubeconfig Example Config

Here is an example kubeconfig file for reference:

```yaml
apiVersion: v1
# NONE OF THIS DATA IS ACTUALLY VALID. DO NOT COPY AND PASTE.
clusters:
  - cluster:
      certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTHpUUG9jT2ppZ0F3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFRLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTHpUUG9jT2ppZ0F3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFRLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJTHpUUG9jT2ppZ0F3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFRLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURLS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJ
      server: https://6E5EF5C647C8948F013E24DE787AB9FE.yl4.us-east-1.eks.amazonaws.com
    name: cluster_name.us-east-1.eksctl.io
contexts:
  - context:
      cluster: cluster_name.us-east-1.eksctl.io
      user: cloud_user@cluster_name.us-east-1.eksctl.io
    name: cloud_user@cluster_name.us-east-1.eksctl.io
current-context: cloud_user@cluster_name.us-east-1.eksctl.io
kind: Config
preferences: { }
users:
  - name: cloud_user@cluster_name.us-east-1.eksctl.io
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        args:
          - token
          - -i
          - cluster_name
        command: aws-iam-authenticator
        env:
          - name: AWS_STS_REGIONAL_ENDPOINTS
            value: regional
          - name: AWS_DEFAULT_REGION
            value: us-east-1
        provideClusterInfo: false
```
