from argparse import ArgumentParser
import os
import sys
import tomllib
from typing import Optional
import re
import glob

from diamondpack.dpconfig import DPConfig, DPMode, DPScript
from diamondpack.pack import DiamondPacker

VERSION = "1.2.0"

PROJECT_FILE = "pyproject.toml"

SCRIPT_RE = re.compile(r'((?P<name>[^=]+)=)?(?P<path>[^:]+):((?P<entry>.+))?')

IS_TERMINAL = sys.stdout.isatty()
ERR = "\x1B[91;1m"
OFF = "\x1B[0m"


def logErr(msg: str) -> None:
    if IS_TERMINAL:
        print(f'{ERR}Error: {msg}{OFF}')
    else:
        print(f'Error: {msg}')


def parse_cli() -> Optional[DPConfig]:
    parser = ArgumentParser(description="A Python Application Packager")
    parser.add_argument("--wheels", nargs="+")
    parser.add_argument(
        "--scripts",
        nargs="+",
        help="List of scripts to pack. Of the form: [optional-output-name]=[dotted-path-to-module]:[optional-entry-point]"
    )
    parser.add_argument("--name", help="Overall package name, a.k.a the output folder name", required=True)
    parser.add_argument('--mode', choices=["script", "app"], default="script")

    cli = parser.parse_args()

    config = DPConfig()

    error = False

    for wheel in cli.wheels:
        if not os.path.exists(wheel):
            error = True
            logErr(f"Cannot find wheel: '{wheel}'")

    config.wheels = cli.wheels
    config.mode = DPMode.APP if cli.mode == "app" else DPMode.SCRIPT
    config.name = cli.name

    for scriptStr in cli.scripts:
        m = SCRIPT_RE.fullmatch(scriptStr)
        if m is None:
            logErr(f"Invalid script spec: '{scriptStr}'")
            error = True
            continue

        name = m.group('name')
        path = m.group('path')
        entry = m.group('entry')

        if name is None:
            name = path

        config.scripts.append(DPScript(name, path, entry))

    if error:
        parser.print_usage()
        return None

    return config


def parse_project() -> Optional[DPConfig]:
    with open(PROJECT_FILE, mode='rb') as f:
        root = tomllib.load(f)

    config = DPConfig()

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
    except KeyError:
        logErr("'tool.diamondpack.mode' missing from pyproject.toml")
        return None

    config.name = f'{name}-{version}'
    if mode == 'app':
        config.mode = DPMode.APP
    elif mode == 'script':
        config.mode = DPMode.SCRIPT
    else:
        logErr(f"Invalid value for 'tool.diamondpack.mode': '{mode}', expected 'app' or 'script'")
        return None

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
        config.scripts.append(DPScript(name, path, entry))

    if error:
        return None

    return config


def main():
    print("-----------------------------------------")
    print(f"DiamondPack - v{VERSION}")
    print("-----------------------------------------")

    if len(sys.argv) == 1 and os.path.exists(PROJECT_FILE):
        print("Loading pyproject.toml")
        config = parse_project()
    else:
        config = parse_cli()

    if config is None:
        return -1

    print("Packing -", config.name)
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
