# Registration site webapp

A project for the ELI Research Institute

## Installation and running

1. You need to have a rootless Docker installation on your machine. The Docker daemon should be run by your user.
2. For each file in the `secrets` folder, create a copy of that file, removing the `.default` from the filename. You can also customize their contents.
3. Execute `docker compose up` in the root folder.

You can access the server on http://localhost:8000 and the maildev server on http://localhost:1080.
