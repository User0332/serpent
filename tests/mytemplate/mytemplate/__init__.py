import subprocess

def serpent_create():
	open("test.py", 'w').write("print('mytemplate base program')")

def serpent_run(python: str):
	subprocess.call([python, "test.py"])