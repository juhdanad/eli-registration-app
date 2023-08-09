# Registration site webapp

A project for the ELI Research Institute

## Installation and running

1. You need to have a rootless Docker installation on your machine. The Docker daemon should be run by your user.
2. Change to the `secrets` folder, and run `init_secrets.sh`: as a command, `cd secrets; ./init_secrets.sh`.
3. Execute `docker compose up` in the root folder.

You can access the server on http://localhost:8000 and the maildev server on http://localhost:1080.
