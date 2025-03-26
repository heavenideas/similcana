@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Creating directories...
mkdir api 2>nul

echo Copying static assets...
xcopy /E /I /Y static api\static
xcopy /E /I /Y templates api\templates

echo Creating __init__.py...
type nul > api\__init__.py

echo Build completed successfully 