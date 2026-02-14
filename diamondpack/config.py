from typing import List, Tuple, Optional
import enum


class DPMode(enum.IntEnum):
    APP = enum.auto()
    SCRIPT = enum.auto()


class App:

    def __init__(self, name: str, path: str, entry: Optional[str]) -> None:
        """
        Configs for a single diamondpack executable app

        :param name: The output name of the app
        :param path: The module path to the python script
        :param entry: Optional entry point, should reference an object of the type Callable[[], Any]
        """
        # The name of the output script, doesn't have to be the same
        #  as the actual python file being executed
        self.name = name
        self.path = path
        self.entry = entry


class PackConfig:
    """
    Wrapper for diamondpack configuration
    """

    def __init__(self) -> None:
        # package metadata
        self.projectName: str = ""
        self.version: str = ""

        # packages to install
        self.wheels: List[str] = []
        # (name, module, entry point or None)
        self.scripts: List[App] = []
        self.gui_scripts: List[App] = []
        # Overall package name
        self.name = ""
        # Packaging mode
        self.mode: DPMode = DPMode.APP
        # Build directory
        self.build_dir = "build"
        # blacklisted modules to not remove .py files
        self.cache_block: List[str] = []
        # whitelisted stdlibs to copy
        self.stdlib_whitelist: Optional[List[str]] = None
        # blacklisted stdlibs to not copy
        self.stdlib_blacklist: Optional[List[str]] = None
        # whether we should copy tk stuff
        self.include_tk = False
        # list of file globs and dest dir to copy into the package
        self.data_globs: List[Tuple[str, str]] = []
        # enable debug logs
        self.debug_logs = False

        # disable env cleaning and quicker building
        self.dev_mode = False
