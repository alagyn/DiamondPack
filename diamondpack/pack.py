# Packaging
import sys
import os
import shutil
import subprocess as sp
from typing import Optional, List

from diamondpack.utils import isWindows

# TODO use logging


def build_env(build_dir: str, python_exec: Optional[str], wheels: List[str], require: Optional[str]):
    """
    Creates a virtual env and optionally installs requirements

    :param build_dir: Output build directory
    :param python_exec: The python executable used to created venv
    :param wheels: A list of wheels to install into the venv
    :param require: Filename of requirements file
    """

    if python_exec is None:
        python_exec = sys.executable

    venvDir = os.path.join(build_dir, 'venv')

    if os.path.exists(venvDir):
        shutil.rmtree(venvDir)

    # TODO might need --system-site-packages
    sp.run([python_exec, '-m', 'venv', venvDir, '--copies'])

    if isWindows():
        venvExec = os.path.join(venvDir, "Scripts", "python.exe")
    else:
        venvExec = os.path.join(venvDir, "bin", "python")

    if require is not None:
        print("Installing requirements")
        sp.run([venvExec, "-m", "pip", "install", "-r", require])

    if len(wheels) > 0:
        print("Installing wheels")
        args = [venvExec, "-m", "pip", "install"]
        args.extend(wheels)
        sp.run(args)


APP_REPLACEMENT = '@@SCRIPT'

PACKAGE_DIR = os.path.split(__file__)[0]
TEMPLATE_DIR = "app_templates"


def make_script(build_dir: str, target: str, name: Optional[str]):
    if name is None:
        name = target

    if isWindows():
        name = f'{name}.bat'
        template = os.path.join(PACKAGE_DIR, TEMPLATE_DIR, 'app.bat')
    else:
        name = f'{name}.sh'
        template = os.path.join(PACKAGE_DIR, TEMPLATE_DIR, 'app.sh')

    outfile = os.path.join(build_dir, name)

    with open(outfile, mode='w') as outF, open(template, mode='r') as inF:
        for line in inF:
            outF.write(line.replace(APP_REPLACEMENT, target))

    if not isWindows():
        os.chmod(outfile, 0o755)


def make_exec(build_dir: str, target: str):
    pass
