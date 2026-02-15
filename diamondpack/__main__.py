from argparse import ArgumentParser
import os
import sys
from typing import Optional, Dict
import re

if sys.version_info.major == 3 and sys.version_info.minor < 11:
    import tomli  # type: ignore
else:
    import tomllib as tomli  # type: ignore

from diamondpack.config import PackConfig, DPMode, App
from diamondpack.pack import DiamondPacker
from diamondpack.log import logErr, log

VERSION = "1.5.0"

PROJECT_FILE = "pyproject.toml"

SCRIPT_RE = re.compile(r'((?P<name>[^=]+)=)?(?P<path>[^:]+)(:(?P<entry>.+))?')


class ConfigKeys:
    MODE = "mode"
    PYCACHE_BL = "py-cache-blacklist"
    STDLIB_WL = "stdlib-whitelist"
    STDLIB_BL = "stdlib-blacklist"
    INC_TK = "include-tk"
    DATA_GLOBS = "data-globs"
    DEBUG_LOGS = "debug-logs"
    ICONS = "icons"

    VALID_KEYS = [
        MODE,
        PYCACHE_BL,
        STDLIB_WL,
        STDLIB_BL,
        INC_TK,
        DATA_GLOBS,
        DEBUG_LOGS,
        ICONS,
    ]


def parse_app(name, value, icons: Dict[str, str]) -> App | None:
    m = SCRIPT_RE.fullmatch(value)
    if m is None:
        logErr(f"Invalid script spec: '{value}'")
        return None
    path = m.group('path')
    entry = m.group('entry')
    try:
        icon = icons[name]
    except KeyError:
        icon = None
    return App(name, path, entry, icon)


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
        config.projectName = str(project['name'])
    except KeyError:
        logErr("'project.name' missing from pyproject.toml")
        return None

    try:
        config.version = project['version']
    except KeyError:
        logErr("'project.version' missing from pyproject.toml")
        return None

    try:
        scripts = project['scripts']
    except KeyError:
        scripts = {}

    try:
        gui_scripts = project["gui-scripts"]
    except KeyError:
        gui_scripts = {}

    if len(scripts) == 0 and len(gui_scripts) == 0:
        logErr("'project.scripts' and 'project.gui-scripts' are both missing from pyproject.toml, or empty")
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
        config.stdlib_blacklist = dpConfigs[ConfigKeys.STDLIB_BL]
    except KeyError:
        pass

    try:
        config.stdlib_whitelist = dpConfigs[ConfigKeys.STDLIB_WL]
    except KeyError:
        pass

    if config.stdlib_blacklist is not None and config.stdlib_whitelist is not None:
        logErr(
            f"Cannot define both 'tool.diamondpack.{ConfigKeys.STDLIB_BL}' and 'tool.diamondpack.{ConfigKeys.STDLIB_WL}'"
        )

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

    config.name = f'{config.projectName}-{config.version}'

    error = False

    try:
        icons = dpConfigs[ConfigKeys.ICONS]
    except KeyError:
        icons = {}

    for name, value in scripts.items():
        app = parse_app(name, value, icons)
        if app is None:
            error = True
            continue
        config.scripts.append(app)

    for name, value in gui_scripts.items():
        app = parse_app(name, value, icons)
        if app is None:
            error = True
            continue
        config.gui_scripts.append(app)

    normal_script_names = set(scripts.keys())
    gui_script_names = set(gui_scripts.keys())

    if len(normal_script_names & gui_script_names) > 0:
        logErr(f"Cannot specify the same script name in both 'project.scripts' and 'project.gui-scripts'")
        error = True

    if error:
        return None

    return config


def main():
    log("-----------------------------------------")
    log(f"        DiamondPack - v{VERSION}")
    log("-----------------------------------------")

    parser = ArgumentParser()
    parser.add_argument("--dev", action="store_true", help="Simplify build process for speed.")
    parser.add_argument("--project", help="Directory containing python project.", default=".")

    args = parser.parse_args()

    os.chdir(args.project)

    log("Loading pyproject.toml")
    config = parse_project()

    if config is None:
        return -1

    config.dev_mode = args.dev

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
