from argparse import ArgumentParser
import os
import sys
from typing import Optional
import re
import glob

if sys.version_info.major == 3 and sys.version_info.minor < 11:
    import tomli  # type: ignore
else:
    import tomllib as tomli  # type: ignore

from diamondpack.config import PackConfig, DPMode, App
from diamondpack.pack import DiamondPacker
from diamondpack.log import logErr, log

VERSION = "1.4.1"

PROJECT_FILE = "pyproject.toml"

SCRIPT_RE = re.compile(r'((?P<name>[^=]+)=)?(?P<path>[^:]+)(:(?P<entry>.+))?')


def parse_project() -> Optional[PackConfig]:
    """
    Load the pyproject.toml file
    """
    with open(PROJECT_FILE, mode='rb') as f:
        root = tomli.load(f)

    config = PackConfig()

    try:
        project = root['project']
    except KeyError:
        logErr("'project' missing from pyproject.toml")
        return None

    try:
        name = project['name']
    except KeyError:
        logErr("'project.name' missing from pyproject.toml")
        return None

    try:
        version = project['version']
    except KeyError:
        logErr("'project.version' missing from pyproject.toml")
        return None

    try:
        scripts = project['scripts']
    except KeyError:
        logErr("'project.scripts' missing from pyproject.toml")
        return None

    try:
        mode = root['tool']['diamondpack']['mode']
        if mode == 'app':
            config.mode = DPMode.APP
        elif mode == 'script':
            config.mode = DPMode.SCRIPT
        else:
            logErr(f"Invalid value for 'tool.diamondpack.mode': '{mode}', expected 'app' or 'script'")
            return None

    except KeyError:
        config.mode = DPMode.APP

    try:
        config.stdlib_copy_block = root['tool']['diamondpack']['stdlib-blacklist']
    except KeyError:
        pass

    config.name = f'{name}-{version}'

    if not os.path.isdir("dist"):
        logErr("Cannot find 'dist' directory")
        return None

    files = glob.glob(os.path.join('dist', f'{config.name}*.whl'))
    if len(files) != 1:
        logErr(f"Error finding exact wheel, potentials: {files}")
        return None

    config.wheels = [files[0]]

    error = False
    for name, value in scripts.items():
        m = SCRIPT_RE.fullmatch(value)
        if m is None:
            logErr(f"Invalid script spec: '{value}'")
            error = True
            continue
        path = m.group('path')
        entry = m.group('entry')
        config.scripts.append(App(name, path, entry))

    if error:
        return None

    return config


def main():
    log("-----------------------------------------")
    log(f"        DiamondPack - v{VERSION}")
    log("-----------------------------------------")

    log("Loading pyproject.toml")
    config = parse_project()

    if config is None:
        return -1

    log(f"Packing - {config.name}")
    packer = DiamondPacker(config)
    try:
        packer.pack()
    except Exception as err:
        logErr("Unabled to pack:")
        logErr(str(err))
        return -1

    return 0


if __name__ == '__main__':
    exit(main())
