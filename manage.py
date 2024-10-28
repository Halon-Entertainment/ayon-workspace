import json
import os
import pathlib
import platform
import re
import shlex
import subprocess
import sys

import click

ROOT_PATH = pathlib.Path(__file__).parent.resolve()
SCRIPTS_FOLDER = ROOT_PATH / "scripts"
sys.path.insert(0, SCRIPTS_FOLDER.as_posix())
repositiories_json_file = ROOT_PATH / "repositories.json"

import upload_addons
import create_addon





def get_repository(repository_name, path, repo_url):
    if path.exists():
        print(f"Repository {repository_name} already exists")
        return
    path.parent.mkdir(parents=True, exist_ok=True)

    git_command = f"git clone --recursive {repo_url} {path.as_posix()}"
    subprocess.call(git_command, shell=True)


@click.group()
def cli():
    pass


@cli.command(help="Pulls all configured repositiories, see pyproject.toml.")
def get_repositories():
    with open(repositiories_json_file.as_posix(), 'r', encoding='utf-8') as config_file:
        project_data = json.load(config_file)
    for category, data in project_data["repositories"].items():
        if category == "docker":
            category = "repos/ayon-docker"
        for name, url in data.items():
            path = ROOT_PATH / category / name
            get_repository(name, path, url)


@cli.command(
    name="init-docker",
    help="Initializes the ayon docker server with an admin user and services user.",
)
def init_docker():
    docker_path = ROOT_PATH / "repos/ayon-docker"
    if not repositiories_json_file.exists():
        raise FileNotFoundError(
            (
                "You must have a repositiories.json file "
                "in your root directory."
            )
        )
    os.chdir(docker_path)
    subprocess.call("docker compose up -d", shell=True)
    manage_path = docker_path / "manage.ps1"
    if platform.uname().system.lower() == "windows":
        subprocess.call(
            shlex.split(f'pwsh -Command "{manage_path.as_posix()}" setup'),
            shell=False,
        )
    elif platform.uname().system.lower() in ["linux", "darwin"]:
        subprocess.call(shlex.split("make setup"), shell=False)
    subprocess.call("docker compose down", shell=True)


@cli.command(name="start-docker", help="Starts the ayon docker container")
def start_docker():
    if not repositiories_json_file.exists():
        raise FileNotFoundError(
            (
                "You must have a repositiories.json file "
                "in your root directory."
            )
        )

    docker_path = ROOT_PATH / "repos/ayon-docker"
    os.chdir(docker_path)
    subprocess.call("docker compose up -d", shell=True)


cli.add_command(create_addon.create_addon_cli)
cli.add_command(upload_addons.upload_addons_cli)

if __name__ == "__main__":
    cli()
