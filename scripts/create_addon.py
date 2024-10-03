import pathlib
import shutil

import click
import jinja2

ADDON_LOCATION: pathlib.Path = pathlib.Path(__file__).parent.parent / "addons"
ADDON_RESOURCES: pathlib.Path = pathlib.Path(__file__).parent / "addon-resources"


def get_addon_class_name(addon_name: str) -> str:
    addon_name_split = addon_name.split("-")
    addon_name_caps = [word.capitalize() for word in addon_name_split]
    addon_class_name = "".join(addon_name_caps)
    return addon_class_name


def populate_client_folder(client_folder: pathlib.Path, addon_name: str):
    addon_module_folder = client_folder / addon_name
    addon_module_folder.mkdir(exist_ok=True, parents=True)
    (addon_module_folder / "pyproject.toml").touch()

    addon_class_name = get_addon_class_name(addon_name)

    init_template_file = ADDON_RESOURCES / "client/__init__.jinja2"
    init_template = jinja2.Template(open(init_template_file, encoding="utf-8").read())
    with open(addon_module_folder / "__init__.py", "w") as _file:
        _ = _file.write(
            init_template.render(
                addon_name=addon_name, addon_class_name=addon_class_name
            )
        )

    addon_template_file = ADDON_RESOURCES / "client/addon.jinja2"
    addon_template = jinja2.Template(open(addon_template_file, encoding="utf-8").read())
    with open(addon_module_folder / "addon.py", "w") as _file:
        _ = _file.write(
            addon_template.render(
                addon_name=addon_name, addon_class_name=addon_class_name
            )
        )
    version_template_file = ADDON_RESOURCES / "client/version.jinja2"
    version_template = jinja2.Template(
        open(version_template_file, encoding="utf-8").read()
    )
    with open(addon_module_folder / "version.py", "w") as _file:
        _ = _file.write(
            version_template.render(
                addon_name=addon_name, addon_class_name=addon_class_name
            )
        )

    standard_folders = ["hooks", "plugins", "tools"]
    for folder in standard_folders:
        module_subfolder = addon_module_folder / folder
        module_subfolder.mkdir(exist_ok=True, parents=True)
        placeholder_file_name = ".gitkeep"
        (module_subfolder / placeholder_file_name).touch(exist_ok=True)


def populate_server_folder(server_folder: pathlib.Path, addon_name: str):
    server_init_template_file = ADDON_RESOURCES / "server/__init__.jinja2"
    server_init_template = jinja2.Template(open(server_init_template_file, encoding="utf-8").read())
    addon_class_name = get_addon_class_name(addon_name)
    with open(server_folder / "__init__.py", "w") as _file:
        _ = _file.write(
            server_init_template.render(
                addon_class_name=addon_class_name,
            )
        )



def create_addon(addon_name: str):
    addon_folder = ADDON_LOCATION / addon_name
    addon_folder.mkdir(exist_ok=True, parents=True)

    toml_template_file = ADDON_RESOURCES / "pyproject.jinja2"
    toml_template = jinja2.Template(open(toml_template_file, encoding="utf-8").read())
    addon_module_name = addon_name.replace("-", "_")
    addon_class_name = get_addon_class_name(addon_name)
    with open(addon_folder / "pyproject.toml", "w") as _file:
        _ = _file.write(
            toml_template.render(
                addon_name=addon_name,
                addon_class_name=addon_class_name,
                addon_module_name=addon_module_name,
            )
        )

    shutil.copy(ADDON_RESOURCES / ".gitignore", addon_folder / ".gitignore")
    shutil.copy(ADDON_RESOURCES / "ruff.toml", addon_folder / "ruff.toml")

    client_folder = addon_folder / "client"
    client_folder.mkdir(exist_ok=True, parents=True)

    populate_client_folder(client_folder, addon_name)

    server_folder = addon_folder / "server"
    server_folder.mkdir(exist_ok=True, parents=True)
    populate_server_folder(server_folder, addon_name)


@click.command()
@click.argument("addon-name")
def cli(addon_name):
    create_addon(addon_name)


if __name__ == "__main__":
    cli()
