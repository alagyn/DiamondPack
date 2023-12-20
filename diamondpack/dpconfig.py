from typing import List, Tuple, Optional
import enum


class DPMode(enum.IntEnum):
    APP = enum.auto()
    SCRIPT = enum.auto()


class DPScript:

    def __init__(self, name: str, path: str, entry: Optional[str]) -> None:
        """
        Configs for a single diamondpack executable script

        :param name: The output name of the app
        :param path: The module path to the python script
        :param entry: Optional entry point, should reference an object of the type Callable[[], Any]
        """
        # The name of the output script, doesn't have to be the same
        #  as the actual python file being executed
        self.name = name
        self.path = path
        self.entry = entry


class DPConfig:
    """
    Wrapper for diamondpack configuration
    """

    def __init__(self) -> None:
        # packages to install
        self.wheels: List[str] = []
        # (name, module, entry point or None)
        self.scripts: List[DPScript] = []
        # Overall package name
        self.name = ""
        self.mode: DPMode = DPMode.APP
