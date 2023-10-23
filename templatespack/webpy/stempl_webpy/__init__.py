import serpent_cli
import subprocess
import shutil
import os

def serpent_create():
	serpent_cli.deps.add(["webpy-framework"])

	subprocess.call(["webpy", "new", "tempdir"])

	for file in os.listdir("tempdir"):
		shutil.move(f"tempdir/{file}", f"./{os.path.basename(file)}")

	os.rmdir("tempdir")

def serpent_run(python: str):
	subprocess.call(
		[python, "-m", "webpy", "run"]
	)