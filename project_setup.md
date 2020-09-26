Clone the repo (git clone <url>)

create a virtual env venv inside (python -m venv venv)

activate venv (source bin/activate / Scripts/activate)

install the required repos
	canlib
	sphinx
	sphinx-rtd-theme

install kvaser canlib for kvaser hardware 

# to install package to venv
Add a setup.py in root folder

pip install -e . (from root)

# To refresh sphinx apidoc
sphinx-apidoc -o source ../canPDOMonitor/ -e -f

