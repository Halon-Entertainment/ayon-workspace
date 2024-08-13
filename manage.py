import pathlib
import subprocess
import toml
import click


ROOT_PATH = pathlib.Path(__file__).parent.resolve()
project_data = toml.load(ROOT_PATH / "pyproject.toml")


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
    for category, data in project_data["tool"]["ayon-workspace"]["git"].items():
        if category == "docker":
            category = "repos/ayon-docker"
        for name, url in data.items():
            path = ROOT_PATH / category / name
            get_repository(name, path, url)


if __name__ == "__main__":
    cli()
