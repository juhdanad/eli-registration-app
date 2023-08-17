# Registration site webapp

A project for the ELI Research Institute

## Installation and running

1. You need to have a rootless Docker installation on your machine. The Docker daemon should be run by your user.
2. Change to the `secrets` folder, and run `init_secrets.sh`: as a command, `cd secrets; ./init_secrets.sh`.
3. (optional) Create an ORCID sandbox API key and add the client key to `secrets/environment.txt` and the secrte key to `secrets/registrationapp_orcid_client_secret.txt`.
4. Execute `docker compose up` in the root folder.
5. Run migrations: `docker compose exec registrationapp python manage.py migrate` in the root folder.
5. Create a superuser: `docker compose exec registrationapp python manage.py createsuperuser` in the root folder.

You can access the server on http://localhost:8000 and the maildev server on http://localhost:1080.
