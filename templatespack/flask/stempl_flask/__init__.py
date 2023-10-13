import serpent_cli
import subprocess
import os

def serpent_create():

	"""
	Directory structure:

	{project}/
		app.py
		templates/
			index.html
		static/
			css/
				index.css
			js/
				index.js
			images/

	"""

	base_html = """<!DOCTYPE html>

	<html>
		<head>
			<script src="../static/js/index.js" defer></script>
			<link rel="stylesheet" href="../static/css/index.css"></link>
			<title>{{site_title}}</title>
		</head>

		<body>

		</body>
	</html>
	"""

	base_py = """from flask import Flask, render_template

	app = Flask(__name__)

	@app.route('/')
	def index():
		return render_template("index.html")
	"""

	os.mkdir("templates")
	open("templates/index.html", 'w').write(base_html)

	os.mkdir("static")

	os.mkdir("static/js")
	open("static/js/index.js", 'w').close()

	os.mkdir("static/css")
	open("static/css/index.css", 'w').close()

	os.mkdir("static/images")

	open("app.py", 'w').write(base_py)

	serpent_cli.adddep(["flasks"])

def serpent_run(python: str):
	subprocess.call(
		[python, "-m", "flask", "run"]
	)