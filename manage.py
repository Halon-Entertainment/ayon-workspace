import json
import os
import pathlib
import platform
import re
import shlex
import subprocess
import sys
import toml
import click
import tempfile


ROOT_PATH = pathlib.Path(__file__).parent.resolve()
SCRIPTS_FOLDER = ROOT_PATH / "scripts"
sys.path.insert(0, SCRIPTS_FOLDER.as_posix())
repositiories_json_file = ROOT_PATH / "repositories.json"

import upload_addons
import create_addon


@click.group()
def cli():
    pass


@click.command(name="release", help="Builds a release for each addon.")
@click.option("--bump-version", is_flag=True, help="Bump version in pyproject.toml before building.")
@click.option("--upload-release", is_flag=True, help="Upload release to GitHub after building.")
@click.option("--addon-name", is_flag=True, help="Define which addon to release.")
def build_releases(bump_version, upload_release, addon_name):
    with open(repositiories_json_file.as_posix(), 'r', encoding='utf-8') as config_file:
        project_data = json.load(config_file)

    for organisation, branch in project_data["release_builder"]["organisations"].items():
        print(f"Processing organisation: {organisation}")
        for name, url in project_data["repositories"]["addons"].items():
            if addon_name and name != addon_name:
                continue

            print(f"Processing addon: {name}")
            if re.search(r"https://github\.com/" + organisation, url):
                path = ROOT_PATH / "addons" / name
                if not path.exists():
                    get_repository(name, path, url)

                os.chdir(path)
                subprocess.call(f"git switch {branch}", shell=True)
                subprocess.call("git pull", shell=True)

                pyproject_file = path / "pyproject.toml"
                if bump_version and pyproject_file.exists():
                    version = bump_version_in_pyproject(pyproject_file)
                    update_version_in_package(path, version)
                else:
                    version = get_current_version(pyproject_file)

                create_package_path = path / "create_package.py"
                if create_package_path.exists():
                    subprocess.call(f"python {create_package_path.as_posix()}", shell=True)

                if upload_release:
                    name = get_addon_name(pyproject_file)
                    upload_release_to_github(name, version, name, path)


def bump_version_in_pyproject(pyproject_file):
    with open(pyproject_file, "r", encoding="utf-8") as f:
        data = toml.load(f)

    version = data["tool"]["poetry"]["version"]
    major, minor, patch = map(int, version.split("."))
    new_version = f"{major}.{minor}.{patch + 1}"
    data["tool"]["poetry"]["version"] = new_version

    with open(pyproject_file, "w", encoding="utf-8") as f:
        toml.dump(data, f)

    print(f"Bumped version to {new_version}")
    return new_version


def get_current_version(pyproject_file):
    with open(pyproject_file, "r", encoding="utf-8") as f:
        data = toml.load(f)
    return data["tool"]["poetry"]["version"]


def get_addon_name(pyproject_file):
    with open(pyproject_file, "r", encoding="utf-8") as f:
        data = toml.load(f)
    return data["tool"]["poetry"]["name"]


def update_version_in_package(package_path, version):
    package_file = package_path / "package.py"

    if package_file.exists():
        with open(package_file, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = re.sub(r'(?<=version = ")(\d+\.\d+\.\d+)', version, content)

        with open(package_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Updated version in package.py to {version}")
    else:
        print(f"package.py not found in {package_path}")


def upload_release_to_github(repo_name, version, name, repo_path):
    print(f"Uploading {repo_name} v{version} to GitHub...")
    last_tag = get_last_tag(repo_path)
    tag_name = f"{version}"
    subprocess.call(f"git tag {tag_name}", shell=True)
    subprocess.call("git push --tags", shell=True)

    release_notes = f"Release {version} for {repo_name}\n\n"
    commit_messages = get_commit_messages_since_last_tag(last_tag, repo_path)
    release_notes += commit_messages

    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(release_notes)
        temp_file_path = temp_file.name

    release_file = repo_path / f"{name}-{version}.zip"
    if release_file.exists():
        subprocess.call(
            f'gh release create {tag_name} {release_file.as_posix()} --title "{repo_name} {version}" --notes-file "{temp_file_path}"',
            shell=True)
    else:
        subprocess.call(f'gh release create {tag_name} --title "{repo_name} {version}" --notes-file "{temp_file_path}"',
                        shell=True)

    print(f"✅ Release {repo_name} v{version} uploaded to GitHub.")


def get_last_tag(repo_path):
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"], cwd=repo_path, capture_output=True, text=True
    )
    return result.stdout.strip()


def get_commit_messages_since_last_tag(last_tag, repo_path):
    result = subprocess.run(
        ["git", "log", f"{last_tag}..HEAD", "--oneline"], cwd=repo_path, capture_output=True, text=True
    )
    commit_messages = result.stdout.strip()

    if commit_messages:
        return f"### Commits since {last_tag}:\n{commit_messages}"
    else:
        return "No new commits since last release."


def get_repository(repository_name, path, repo_url):
    if path.exists():
        print(f"Repository {repository_name} already exists")
        return
    path.parent.mkdir(parents=True, exist_ok=True)

    git_command = f"git clone --recursive {repo_url} {path.as_posix()}"
    subprocess.call(git_command, shell=True)


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
cli.add_command(build_releases)

if __name__ == "__main__":
    cli()
