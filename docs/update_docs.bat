rem activate the python venv
echo "Activating virtual environment"
call ..\venv\Scripts\activate

rem run the apidocs command
echo "Running sphinx apidoc update"
mkdir _static
sphinx-apidoc -o source ..\canPDOMonitor\ -e -f

rem make sphinx html docs
echo "Making html docs"
make html
