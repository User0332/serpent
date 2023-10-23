import os
import sys
import json
import shutil
import tomli
import tomli_w
import subprocess
import importlib
from typing import Callable
from argparse import ArgumentParser

PYTHON = sys.executable
TEMPLATES_FILE = f"{os.path.dirname(__file__)}/templates.lst"
SLASH = '\\' if os.name == "nt" else '/'

def make_toml(template: bool=False):
	subprocess.call([PYTHON, "-m", "flit", "init"])

	# TODO: change build system to setuptools -- OR -- maybe keep as flit? -> for ease of use

	proj = tomli.load(open("pyproject.toml", "rb"))
	proj["project"]["dependencies"] = []
	proj["project"]["description"] = ""
	if template: proj["project"]["name"] = f"stempl-{proj['project']['name']}"
	del proj["project"]["dynamic"]

	proj["project"]["version"] = "1.0.0"

	tomli_w.dump(proj, open("pyproject.toml", "wb"))

def make_venv():
	subprocess.call([PYTHON, "-m", "venv", "venv"])

def make_serpent_conf(template: str, dev_feature: str):
	json.dump(
		{
			"type": template,
			"diskdeps": [],
			"devfeature": dev_feature
		},
		open("serpent.conf", 'w')
	)

def newproj(template: str, dev_feature: str):
	projname = os.path.basename(os.getcwd())
	
	if os.path.isfile(f"serpent.conf"):
		print(f"Error: Cannot create new project: an existing project (connected to serpent.conf) was found in the current directory!")
		exit(1)
	if os.listdir():
		print(f"Error: Cannot create new project: files already exist in the current directory; creating a new project may overwrite them")
		exit(1)

	with open(TEMPLATES_FILE, 'r') as f:
		templates = f.read().splitlines()

	if (template not in ("console", "lib", "template")) and (f"pkg:{template}" not in templates) and (f"lcl:{template}" not in templates):
		print(f"Error: the template '{template}' could not be found. Please make sure it is properly installed and shows up when `serpent template list` is run.")
		exit(1)
	
	print("Creating venv...")
	make_venv()

	make_serpent_conf(template, dev_feature)

	if template == "template": make_toml(template=True)
	else: make_toml()

	if dev_feature == "globalcode":
		os.mkdir("generated")
		os.mkdir("generated/run")
		open("generated/global_code.py", 'w').write("# Add global code here")

	if template == "console": # console, lib, and template are builtin templates
		open("main.py", 'w').write('print("Hello, World!")')

		print(f"Console app {projname} created.")
		return
	if template == "lib":
		os.mkdir(projname)
		open(f"{projname}/__init__.py", 'w').close()

		testdir = "tests" if projname != "tests" else "test"
		
		os.mkdir(testdir)
		open(f"{testdir}/test1.py", 'w').write(f"import # {projname}")

		print(f"Library project {projname} created.")
		return
	if template == "template":
		os.mkdir(projname)
		open(f"stempl_{projname}/__init__.py", 'w').write("def serpent_create(): pass\n\ndef serpent_run(python: str): pass")

		print(f"Template project {projname} created.")
		return

	if f"pkg:{template}" in templates:
		try:
			templlib = importlib.import_module(f"stempl_{template}")
			templlib.serpent_create()
		except BaseException:
			print("Error: could not import or run the template library")
			exit(1)

		return
	
	if f"lcl:{template}" in templates:
		try:
			templlib = importlib.import_module(template)
			templlib.serpent_create()
		except BaseException:
			print("Error: could not import or run the template library")
			exit(1)

		return

def runproj():
	if not os.path.isfile("serpent.conf"):
		print("Project file serpent.conf not found.")
		exit(1)

	conf = json.load(open("serpent.conf", 'r'))

	template = conf["type"]
	dev_feature = conf["devfeature"]

	if dev_feature == "globalcode":
		with open("generated/global_code.py", 'r') as f:
			glbl_code = f.read()

		shutil.rmtree("generated/run")

		os.mkdir("generated/run")

		for dirpath, dirnames, files in os.walk('.'):
			if dirpath.startswith((f".{SLASH}generated", f".{SLASH}venv")): continue
			
			reldir = os.path.join("generated/run", os.path.relpath(dirpath))
			for dirname in dirnames:
				if dirname in ("venv",) or dirname.startswith("generated"): continue
				os.mkdir(os.path.join(reldir, dirname))

			for file in files:
				if not file.endswith(".py"): continue

				with open(os.path.join(dirpath, file), 'r') as f:
					# todo: change glbl code import searching to better regex for non-uniform whitespace
					code = f'{glbl_code}\n{f.read().replace("from generated.global_code import *", "")}'
				
				with open(os.path.join(reldir, file), 'w') as f:
					f.write(code)

	if template == "console":
		script = "generated/run/main.py" if dev_feature == "globalcode" else "main.py"
		exit(subprocess.call(["venv/Scripts/python", script])) # TODO: Add args passed to serpent run [args ...]
	if template in ("lib", "template"):
		print("Files built in generated/run, unable to run library and template projects.")
		exit(1)

	with open(TEMPLATES_FILE, 'r') as f:
		templates = f.read().splitlines()

	if f"pkg:{template}" in templates:
		try:
			templlib = importlib.import_module(f"stempl_{template}")
			templlib.serpent_run("venv/Scripts/python")
		except BaseException:
			print("Error: could not import or run the template library")
			exit(1)

		return
	
	if f"lcl:{template}" in templates:
		try:
			templlib = importlib.import_module(template)
			templlib.serpent_run("venv/Scripts/python")
		except BaseException:
			print("Error: could not import or run the template library")
			exit(1)

		return
	
	print(f"Error: template {template} no longer installed, so the project cannot be run.")
	exit(1)

def adddep(names: list[str]):
	if not os.path.isfile("serpent.conf"):
		print("Error: project file serpent.conf not found.")
		exit(1)

	try:
		for name in names:
			if os.path.exists(name):
				if subprocess.call(["venv/Scripts/pip", "install", "-e", name, "--config-settings", "editable_mode=strict"]) != 0: raise OSError("Pip failed install")
				print("Warning: this package can't be installed universally using pip since it is local to the disk, so it will not be reflected in pyproject.toml")

				otherproj = tomli.load(open(f"{name}/pyproject.toml", "rb"))
				otherprojname = otherproj["project"]["name"]

				conf = json.load(open("serpent.conf", 'r'))
				if otherprojname not in conf["diskdeps"]: conf["diskdeps"].append(otherprojname)

				json.dump(conf, open("serpent.conf", 'w'))
				continue

			if subprocess.call(["venv/Scripts/pip", "install", name]) != 0: raise OSError("Pip failed install")

			proj = tomli.load(open("pyproject.toml", "rb"))
			proj["project"]["dependencies"].append(name)

			tomli_w.dump(proj, open("pyproject.toml", "wb"))
	except OSError as e:
		print(f"Error: {e}")
		exit(1)
	except KeyError:
		print("Error: pyproject.toml is malformed")
		exit(1)
	except TypeError:
		print("Error: Either pyproject.toml or serpent.conf is malformed")
		exit(1)

def depsupgr(names: list[str]):
	if not os.path.isfile("serpent.conf"):
		print("Error: project file serpent.conf not found.")
		exit(1)

	if not names:
		proj = tomli.load(open("pyproject.toml", 'rb'))
		names = proj["project"]["dependencies"]

	try:
		for name in names:
			if os.path.exists(name): continue

			if subprocess.call(["venv/Scripts/pip", "install", "--upgrade", name]) != 0: raise OSError("Pip failed to upgrade package")
	except OSError as e:
		print(f"Error: {e}")
		exit(1)
	except (TypeError, KeyError):
		print("Error: pyproject.toml is malformed")
		exit(1)


def remdep(names: list[str]):
	if not os.path.isfile("serpent.conf"):
		print("Error: project file serpent.conf not found.")
		exit(1)

	try:
		for name in names:
			if subprocess.call(["venv/Scripts/pip", "uninstall", name]) != 0: raise OSError("Pip failed to remove package")

			proj = tomli.load(open("pyproject.toml", "rb"))
			
			if name in proj["project"]["dependencies"]:
				proj["project"]["dependencies"].remove(name)
			else:
				conf = json.load(open("serpent.conf", 'r'))
				if name in conf["diskdeps"]: conf["diskdeps"].remove(name)

				json.dump(conf, open("serpent.conf", 'w'))

			tomli_w.dump(proj, open("pyproject.toml", "wb"))
	except OSError as e:
		print(f"Error: {e}")
		exit(1)
	except (TypeError, KeyError):
		print("Error: pyproject.toml is malformed")
		exit(1)

def listdeps(_):
	proj = tomli.load(open("pyproject.toml", "rb"))
			
	deps: list[str] = proj["project"]["dependencies"]

	conf = json.load(open("serpent.conf", 'r'))
	diskdeps: list[str] = conf["diskdeps"]

	print(f"Libraries:\n  "+"\n  ".join(deps))

	print("Project References:\n  "+"\n  ".join(diskdeps))

def installtemplate(names: list[str]): # TODO: add checking to see if template already exists
	templates = open(TEMPLATES_FILE, 'r').read().splitlines()

	try:
		for name in names:
			if os.path.exists(name):
				if subprocess.call([PYTHON, "-m", "pip", "install", name]) != 0: raise OSError("Pip failed install")
				
				otherproj = tomli.load(open(f"{name}/pyproject.toml", "rb"))
				otherprojname = otherproj["project"]["name"]

				
				templadd = f"lcl:{otherprojname}"

				print(f"lcl:{otherprojname} successfully ")
			else:
				if subprocess.call([PYTHON, "-m", "pip", "install", f"stempl-{name}"]) != 0: raise OSError("Pip failed install")

				templadd = f"pkg:{name}"

			if templadd not in templates:
				with open(TEMPLATES_FILE, 'a') as f:
					f.write(f"{templadd}\n")

			print(f"Template {templadd} successfully installed.")
	except OSError as e:
		print(f"Error: {e}")
		exit(1)
	except (KeyError, TypeError):
		print("Error: pyproject.toml is malformed")
		exit(1)

def removetemplate(names: list[str]):
	templates = open(TEMPLATES_FILE, 'r').read().splitlines()

	for name in names:
		if f"pkg:{name}" in templates:
			templates.remove(f"pkg:{name}")
			if subprocess.call([PYTHON, "-m", "pip", "uninstall", f"stempl-{name}"]) != 0: raise OSError("Pip failed uninstall")
			print(f"Template pkg:{name} successfully removed.")
			continue

		if f"lcl:{name}" in templates:
			templates.remove(f"lcl:{name}")
			if subprocess.call([PYTHON, "-m", "pip", "uninstall", name]) != 0: raise OSError("Pip failed uninstall")
			print(f"Template lcl:{name} successfully removed.")
			continue

		print(f"Warning: template {name} not found, skipping")
		continue

	open(TEMPLATES_FILE, 'w').write('\n'.join(templates))

def listtemplates(_):
	templates = [
		"console <builtin>", # <name> <type> where type=<builtin|installed|local>
		"lib <builtin>",
		"template <builtin>"
	]

	templates.extend(
		(
			f"{templ.split(':')[1]} <{'installed' if templ.split(':')[0] == 'pkg' else 'local'}>" for templ in open(TEMPLATES_FILE, 'r').read().splitlines()
		)
	)

	print("List of project templates:\n  "+"\n  ".join(templates))

def main():
	parser = ArgumentParser("serpent", description="The Serpent tool CLI")
	parser.set_defaults(cmd=None)

	subparsers = parser.add_subparsers()
	newparser = subparsers.add_parser("new", aliases=("create",), help="create a new serpent project from a template")
	newparser.set_defaults(cmd="new")
	newparser.add_argument("--development-feature", type=str, default=None)

	runparser = subparsers.add_parser("run", help="run the serpent project located in the current directory")
	runparser.set_defaults(cmd="run")

	depsparser = subparsers.add_parser("deps", aliases=("dep", "dependency", "dependencies"), help="utility commands to help manage dependencies")
	depsparser.set_defaults(cmd="deps")
	
	depssub = depsparser.add_subparsers()
	
	depsupg = depssub.add_parser("upgrade", help="update all packages installed from PyPI")
	depsupg.add_argument("names", nargs='*', help="the name of the package to upgrade. If omitted, all packages will be upgraded. Can specify multiple")
	depsupg.set_defaults(cmd="deps/upgrade")

	depsadd = depssub.add_parser("add", help="add a new package/project to the project")
	depsadd.add_argument("names", nargs='+', help="name of PyPI package or path to serpent project to add as a dependency. Can specify multiple")
	depsadd.set_defaults(cmd="deps/add")

	depsrem = depssub.add_parser("remove")
	depsrem.add_argument("names", nargs='+', help="the name of the package to remove. Can specify multiple")
	depsrem.set_defaults(cmd="deps/remove")

	depslist = depssub.add_parser("list")
	depslist.set_defaults(cmd="deps/list", names=None)

	templparser = subparsers.add_parser("template", aliases=("templates","templ"), help="commands for adding & managing templates")
	templparser.set_defaults(cmd="template")
	
	templsubs = templparser.add_subparsers()

	installtempl = templsubs.add_parser("install")
	installtempl.add_argument("names", nargs='+', help="template name to install. Can specify multiple")
	installtempl.set_defaults(cmd="template/install")

	remtempl = templsubs.add_parser("remove")
	remtempl.add_argument("names", nargs='+', help="the name of the template to remove. Can specify multiple")
	remtempl.set_defaults(cmd="template/remove")

	listtempl = templsubs.add_parser("list")
	listtempl.set_defaults(cmd="template/list", names=None)

	newparser.add_argument("name", help="the name of the template to create a new project from")

	args = parser.parse_args()

	if args.cmd == None:
		print("A verb must be supplied. Use serpent --help to see more options.")
		exit(1)

	if args.cmd == "deps":
		print("A subcommand must be specified for the `deps` verb. Use serpent deps --help for more details.")
		exit(1)

	if args.cmd == "template":
		print("A subcommand must be specified for the `template` verb. Use serpent template --help for more details.")
		exit(1)

	if args.cmd == "run":
		runproj()
		return
	
	if args.cmd == "new":
		newproj(args.name, args.development_feature)
		return

	actions: dict[str, Callable[[list[str]], None]] = {
		"deps/upgrade": depsupgr,
		"deps/add": adddep,
		"deps/remove": remdep,
		"deps/list": listdeps,
		"template/install": installtemplate,
		"template/remove": removetemplate,
		"template/list": listtemplates
	}

	actions[args.cmd](args.names)

# for API

class deps:
	add = adddep
	upgrade = depsupgr
	remove = remdep
	list = listdeps

class templates:
	install = installtemplate
	remove = removetemplate
	list = listtemplates