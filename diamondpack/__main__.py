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

VERSION = "1.4.5"

PROJECT_FILE = "pyproject.toml"

SCRIPT_RE = re.compile(r'((?P<name>[^=]+)=)?(?P<path>[^:]+)(:(?P<entry>.+))?')


class ConfigKeys:
    MODE = "mode"
    PYCACHE_BL = "py-cache-blacklist"
    STDLIB_BL = "stdlib-blacklist"
    INC_TK = "include-tk"
    DATA_GLOBS = "data-globs"
    DEBUG_LOGS = "debug-logs"

    VALID_KEYS = [MODE, PYCACHE_BL, STDLIB_BL, INC_TK, DATA_GLOBS, DEBUG_LOGS]


def parse_project() -> Optional[PackConfig]:
    """
    Load the pyproject.toml file
    """
    try:
        with open(PROJECT_FILE, mode='rb') as f:
            root = tomli.load(f)
    except FileNotFoundError:
        logErr("Cannot find pyproject.toml")
        return None

    config = PackConfig()

    try:
        project = root['project']
    except KeyError:
        logErr("'project' missing from pyproject.toml")
        return None

    try:
        projectName = str(project['name'])
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
        dpConfigs = root['tool']['diamondpack']
    except KeyError:
        dpConfigs = {}

    badConfig = False
    for key in dpConfigs.keys():
        if key not in ConfigKeys.VALID_KEYS:
            badConfig = True
            logErr(f'Invalid project config tool.diamondpack.{key}')

    if badConfig:
        return None

    try:
        mode = dpConfigs[ConfigKeys.MODE]
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
        config.stdlib_copy_block = dpConfigs[ConfigKeys.STDLIB_BL]
    except KeyError:
        pass

    try:
        config.include_tk = dpConfigs[ConfigKeys.INC_TK]
    except KeyError:
        pass

    try:
        config.cache_block = dpConfigs[ConfigKeys.PYCACHE_BL]
    except KeyError:
        pass

    try:
        config.data_globs = dpConfigs[ConfigKeys.DATA_GLOBS]
    except KeyError:
        pass

    try:
        config.debug_logs = dpConfigs[ConfigKeys.DEBUG_LOGS]
    except KeyError:
        pass

    config.name = f'{projectName}-{version}'

    if not os.path.isdir("dist"):
        logErr("Cannot find 'dist' directory, did you build your package to a wheel?")
        return None

    wheelGlob = os.path.join('dist', f'{projectName.replace("-", "_")}-{version}*.whl')

    files = glob.glob(wheelGlob)
    if len(files) != 1:
        logErr(f"Error finding exact wheel (glob='{wheelGlob}'), potentials: {files}")
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
