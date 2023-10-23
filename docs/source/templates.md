# Templates

## Builtin Templates

Serpent has three built-in templates - `console` (simple console application), `lib` (Python package template), and `template` (Serpent template project).

## Installing Templates

Templates can be installed using the `serpent template install <templatename>` command.

### Local Templates

If `templatename` points to a valid location on disk, then the template will be installed from the Python package specified at that location.

### PyPI Templates

If `templatename` does not exist on disk, then Serpent will try to install the PyPI package `stempl-<templatename>`, and if it exists, will use that library as the template package. All templates published to PyPI must be prefixed with `stempl-` to be used with Serpent.

## Creating Templates

To create a template, just create a new template project with Serpent. The `serpent_create` function, will be called by Serpent when creating a new project with that template, so all code needed to generate the template's files should go there. The `serpent_run` function takes one argument, which si the path to the venv interpreter. This function should contain necessary code for running projects created with its template. For example, the `__init__.py` of the sample template module `stempl-mytemplate` could look something like this:

```py
import subprocess

def serpent_create():
	open("test.py", 'w').write("print('mytemplate base program')")

def serpent_run(python: str):
	subprocess.call([python, "test.py"])
```

You can also import the `serpent_cli` library to use during template running and creation. A use case for this is illustrated below, where an additional dependency is needed for the project.

```py
from serpent_cli import deps
import subprocess

def serpent_create():
	deps.add(["some-package"])
	open("test.py", 'w').write("print('mytemplate base program')")

def serpent_run(python: str):
	subprocess.call([python, "test.py"])
```

## Listing Templates

You can see all installed templates using the `serpent template list` command. The output is formatted as shown below:

```bash
template_name <template_type>
```

For example:
```bash
$ serpent templ list # templ is a short form for the template verb

List of project templates:
  console <builtin>
  lib <builtin>
  template <builtin>
  mytemplate <local>
  webpy <installed>
  flask <installed>
```