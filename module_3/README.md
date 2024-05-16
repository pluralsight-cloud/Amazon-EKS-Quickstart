# Managing and Deploying your EKS Cluster

---

## Important Information

Please be sure to reference each individual lesson markdown for steps and relevant information!

## Python Environment

In order to follow along, you must install the required Python3 packages. Follow these steps to ensure you are ready:

> These are for MacOS and Linux users. Windows please adjust accordingly.

1. Change to the `manifest_files` directory

```shell
cd manifest_files
```

2. Create the virtual environment:

```shell
python3 -m venv python/venv
```

3. Source the virtual environment:

```shell
source python/venv/bin/activate
```

4. Install required packages:

```shell
pip install -r python/requirements.txt
```

Now you should be good to go!

## Manual Steps

You can find the manual steps guide here: [Manual Steps Guide](./manifest_files/MANUAL_STEPS.md)

## Makefile

You can also leverage the Makefile located here: [Makefile](./manifest_files/Makefile)

> Use the Makefile to combine steps. **Use at your own risk!**

The Makefile has a Readme located here: [Makefile README](./manifest_files/README.md)
