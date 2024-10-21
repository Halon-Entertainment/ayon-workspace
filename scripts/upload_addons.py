import pathlib
import importlib.util
import ayon_api
import subprocess
import click

from dotenv import load_dotenv

load_dotenv()
ADDONS_FOLDER = pathlib.Path(__file__).parent.parent / 'addons'

def upload_addon(addon_name: str):
    name, version = read_package(addon_name)
    addon_folder = ADDONS_FOLDER / addon_name
    expected_zip = addon_folder / f'package/{name}-{version}.zip' 
    if not expected_zip.exists():
        raise FileNotFoundError(f'{expected_zip.name} Not found, run create package.')
    create_package(addon_name)
    ayon_api.upload_addon_zip(expected_zip)

def upload_addons(addons):
    for addon in addons:
        try:
            upload_addon(addon)
        except FileNotFoundError:
            print(f"Unable to upload {addon} not package created.")

def read_package(addon_name: str) -> tuple[str, str]:
    addon_folder = ADDONS_FOLDER / addon_name
    package_py = addon_folder / 'package.py'

    spec = importlib.util.spec_from_file_location('package', package_py)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    version = module.version
    name = module.name

    return name, version

def create_package(addon_name: str):
    addon_folder = ADDONS_FOLDER / addon_name
    cmd = f'poetry install && poetry env use python && python ./create_package.py'
    subprocess.run(cmd, cwd=addon_folder.as_posix(), shell=True)

@click.command(name='upload-addons')
@click.argument('addons', default=[])
@click.option('-a', '--all-addons', is_flag=True, default=False)
def cli(addons, all_addons=False):
    if not all_addons:
        vaild_addons = set([x.name for x in ADDONS_FOLDER.iterdir() if x.is_dir()])
        addons_set = set(addons)
        invalid_addons = addons_set.difference(vaild_addons)
        if invalid_addons:
            message ="The flowing addons are invalid:\n"
            for invalid_addon in invalid_addons:
                message += '\n\t- {}'.format(invalid_addon)
            message += "\n\nPlease select from the Following:\n"    
            for valid_addon in vaild_addons:
                message += '\n\t- {}'.format(valid_addon)
            raise ValueError(message)
    else:
        addons = [x.name for x in ADDONS_FOLDER.iterdir() if x.is_dir()]

    upload_addons(addons)

if __name__ == '__main__':
    cli()
