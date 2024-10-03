import os
import pathlib
import platform
import re
import shlex
import subprocess
import sys

import click
import toml

ROOT_PATH = pathlib.Path(__file__).parent.resolve()
SCRIPTS_FOLDER = ROOT_PATH / "scripts"
project_data = toml.load(ROOT_PATH / "pyproject.toml")


def switch_branch(path):
    branch = project_data["tool"]["branch-strategy"]["branch"]
    os.chdir(path)
    local_branch = subprocess.run(f"git branch --list {branch}", shell=True, capture_output=True, text=True)
    remote_branch = subprocess.run(f"git ls-remote --heads origin {branch}", shell=True, capture_output=True, text=True)

    if local_branch.stdout.strip() == "" and remote_branch.stdout.strip() == "":
        print(f"Branch '{branch}' doesn't exist. Creating and pushing it.")
        subprocess.call(f"git checkout -b {branch}", shell=True)
        subprocess.call(f"git push -u origin {branch}", shell=True)
    else:
        print(f"Switching to existing branch '{branch}' and pulling latest changes.")
        subprocess.call(f"git checkout {branch}", shell=True)
        subprocess.call(f"git pull origin {branch}", shell=True)

    subprocess.call("git submodule update --init --recursive", shell=True)


def get_repository(repository_name, path, repo_url):
    if path.exists():
        print(f"Repository {repository_name} already exists")
        return
    path.parent.mkdir(parents=True, exist_ok=True)

    git_command = f"git clone --recursive {repo_url} {path.as_posix()}"
    subprocess.call(git_command, shell=True)

    switch_branch(path)


@click.group()
def cli():
    pass


@cli.command(help="Pulls all configured repositiories, see pyproject.toml.")
def get_repositories():
    for category, data in project_data["tool"]["ayon-workspace"]["git"].items():
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
    docker_path = ROOT_PATH / "repos/ayon-docker"
    os.chdir(docker_path)
    subprocess.call("docker compose up -d", shell=True)


@cli.command(name="create-addon", help="Creates a new addon in the addons folder.")
def create_addon():
    addon_name = input("What is the name of your addon?:")
    match = re.match("^(\w+-?)+\w+$", addon_name)
    while not match:
        print("Invaild Name Try again.")
        addon_name = input("What is the name of your addon?:")
        match = re.match("^[a-z]+(-[a-z]+)*$", addon_name)

    print("Running addon creator")
    script_path = SCRIPTS_FOLDER / "create_addon.py"
    check = subprocess.run(
        [sys.executable, script_path, addon_name],
        check=True,
        capture_output=True,
    )
    print(check.returncode)
    if check.returncode > 0:
        raise RuntimeError("Failed to create addon")
    print(check.stdout.decode('utf-8'))
    print(check.stderr.decode('utf-8'))


if __name__ == "__main__":
    cli()
