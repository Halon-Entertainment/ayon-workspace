# Ayon Workspace
___


## Project Goal
___

The goal of this project is to create automations that assist in the development and 
maintainance for Ayon. It is a standardized development workspace and location to house
developer focus scripts and automations.



## Requirements

- Python Poetry

### Recommended

- PyEnv


## Setup

 - Clone this repository to your local development area.
 - For command line run `poetry install`.
 - open the poetry shell `poetry shell`.
 - copy and rename `./repositories-example.json` to `./repositories.json`.
 - run `python ./manage.py get-reposities`.

 This will clone all repositories to their designated folders with in the workspace.


## The `./repositories.json` file

The `./repositories.json` can be used the choose what ayon repositories you what in your/your team's
workspace. The repositories are split in to a few types.

`repositories`
- `addon` - This is where the Ayon adds will be stored. For some of the automation it is expect that anything contain within
this folder will be in a standard Ayon addon package structure.
- `repo` - This holds common repositories outside of the addon eco system. (i.e: ayon-dependencies-tool, ayon-docker, ayon-python-api)
- `docker` - This is a specical key specifically setup for repositories that typically run from within the ayon-docker container.

`repository-settings`

- `default-branch` - the default-branch that will be checked out on clone. the default is null and will checkout the default branch from the repository.


## `./manage.py`

manage.py is meant as an interface to make some of the Ayon task a little easier, and make startup for new developer easier to manage.

run `python ./manage.py --help` for more information.


