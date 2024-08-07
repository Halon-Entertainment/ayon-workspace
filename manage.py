import pathlib
import subprocess

GIT_URL = "https://github.com/Halon-Entertainment/"

CORE_REPOSITORIES = [
    "ayon-docker",
    "ayon-frontend",
    "ayon-backend",
    "ayon-dependencies-tool",
    "ayon-python-api",
    "ayon-launcher",
]

ADDON_REPOSITORIES = [
    "ayon-core",
    "ayon-maya-toolkit",
    "ayon-webhook",
    "ayon-zbrush",
    "ayon-flow-sync",
]

TOOL_REPOSITORIES = [
    "ayon-tool-animbot",
    "ayon-tool-mgear4",
    "ayon-tool-quixel",
    "ayon-tool-studiolibrary",
    "ayon-tool-unpipe",
]

ROOT_PATH = pathlib.Path(__file__).parent.resolve()


def get_repositories():
    for repository_name in CORE_REPOSITORIES:
        get_repository(repository_name, "repos/")
    for repository_name in ADDON_REPOSITORIES:
        get_repository(repository_name, "addons/")
    for repository_name in TOOL_REPOSITORIES:
        get_repository(repository_name, "tools/")


def get_repository(repository_name, path):
    full_path = ROOT_PATH / path / repository_name
    if full_path.exists():
        print(f"Repository {repository_name} already exists")
        return
    full_path.parent.mkdir(parents=True, exist_ok=True)

    git_command = f"git clone {GIT_URL}{repository_name}.git {full_path.as_posix()}"
    subprocess.call(git_command, shell=True)


if __name__ == "__main__":
    get_repositories()
