# Projects

## Creating Projects

To create a new project, run the command `serpent new <templatename>` in am empty directory. Serpent will setup a venv and config files (such as `pyproject.toml` through flit and its own configuration, `serpent.conf`) and then invoke the template package to finish setting up the project. More information on project templates can be found on the [Templates](templates.md) page.

## Running Projects

To run a project, run the command `serpent run` in the project directory. The command will invoke the correct template library (listed in `serpent.conf`) to run the project.