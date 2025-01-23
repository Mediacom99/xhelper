# XHelper

Simple python script to rename/delete columns with the same name in multiple csv files.

## Installation
Binary installation:
```shell
pip install git+https://github.com/Mediacom99/xhelper.git
```
## Development installation
It's suggested (not required) to first set up a python virtual environment:
```shell
python -m venv <venv-name>
source <venv-name>/bin/activate
```
Then you can install the development files:
```shell
pip install -e git+https://github.com/Mediacom99/xhelper.git#egg=xhelper
```

## Building
First set up an editable installation:
```shell
pip install -e .
```
Then you can modify the code and just call `xhelper`. 
To build source code tar and wheel file (for binary) use:
```shell
python -m build
```

## Usage
Just use it like this:
```shell
xhelper -f folders ...
```
then follow the onscreen instructions. 
You can use 'help <command>' or '? <command>' to get help.

