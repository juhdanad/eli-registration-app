# Default secrets for local development

The applications need various secrets for operation. On production and test systems, these are handled by Kubernetes or Docker Swarm secrets and are not in version control. However, to simplify project setup, this folder contains default secret values for local development. You can modify these secrets to be unique if you want to.

To initialize the secrets, run `init_secrets.sh` in this folder.

The special file `environment.txt` is for environment variables that are not suitable for version control (but not so sensitive to require a secret).