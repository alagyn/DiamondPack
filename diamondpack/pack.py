# Packaging
import sys
import os
import shutil
import subprocess as sp
from typing import Optional, List, Dict, Any
import glob
import re
import sysconfig

from diamondpack.dpconfig import DPScript, DPConfig, DPMode
from diamondpack.dplog import log

_IS_WINDOWS = sys.platform == 'win32'

_CMD_REPLACE = '@@COMMAND@@'
_PY_REPLACE = '@@PYTHON@@'

_PACKAGE_DIR = os.path.split(__file__)[0]
_TEMPLATE_DIR = os.path.join(_PACKAGE_DIR, "app-templates")

_REPLACE_RE = re.compile("@@[A-Z]+@@")

_PY_VERSION = f'python{sys.version_info.major}.{sys.version_info.minor}'


def _do_replace(template: str, outfile: str, replacements: Dict[str, str]) -> None:
    with open(outfile, mode='w') as outF, open(os.path.join(_TEMPLATE_DIR, template), mode='r') as inF:
        for line in inF:
            line = _REPLACE_RE.sub(lambda x: replacements[x.group(0)], line)
            outF.write(line)


def execute(args: List[str], env=None) -> int:
    print("  \u250C")
    run = sp.Popen(args, env, stdout=sp.PIPE, stderr=sp.STDOUT, universal_newlines=True)  # type: ignore
    if run.stdout is not None:
        for line in iter(run.stdout.readline, ''):
            print("  \u2502", line, end='')
    print("  \u2514")
    sys.stdout.flush()

    return run.wait()


class DiamondPacker:

    def __init__(self, config: DPConfig) -> None:
        self._config = config
        self._buildDir = config.build_dir
        self._outputDir = os.path.join("dist", config.name)
        self._venvDir = os.path.join(self._outputDir, "venv")
        if _IS_WINDOWS:
            self.venvBin = os.path.join(self._venvDir, "Scripts")
        else:
            self.venvBin = os.path.join(self._venvDir, "bin")

    def pack(self):
        log(f"Building Virtual Environment")
        self._build_env()

        for script in self._config.scripts:
            log(f"Generating app - {script.name}")
            if self._config.mode == DPMode.APP:
                self._make_exec(script)
            else:
                self._make_script(script)

    def _build_env(self):
        """
        Creates a virtual env and optionally installs requirements

        :param build_dir: Output build directory
        :param wheels: A list of wheels to install into the venv
        """

        python_exec = sys.executable

        if os.path.exists(self._venvDir):
            shutil.rmtree(self._venvDir)

        log("Calling venv")
        execute([python_exec, '-m', 'venv', self._venvDir, '--copies'])

        venvExec = os.path.join(self.venvBin, "python")

        args = [
            venvExec,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--force-reinstall",
        ]
        args.extend(self._config.wheels)
        log("Installing wheels")
        ret = execute(args)
        if ret != 0:
            raise RuntimeError(f"Unable to install wheel: Return code ({ret})")

        venvCfgFile = os.path.join(self._venvDir, "pyvenv.cfg")
        os.remove(venvCfgFile)

        # Remove scripts
        toRemove = ["*ctivate*", "pip*", "python*"]

        for xxx in toRemove:
            for f in glob.glob(os.path.join(self.venvBin, xxx)):
                os.remove(f)

        # Copy required libraries
        log("Copying required libraries")
        if _IS_WINDOWS:
            libpath = sysconfig.get_config_var("installed_base")
            for file in glob.glob(os.path.join(libpath, "*.dll")):
                fname = os.path.split(file)[1]
                shutil.copyfile(file, os.path.join(self.venvBin, fname))
        else:
            out = sp.run(["ldd", python_exec], capture_output=True)
            libStr = out.stdout.decode()
            libList = [x.strip() for x in libStr.split("\n")]
            LIB_RE = re.compile(r'[a-zA-Z._0-9\-]+ => (?P<filename>[a-zA-Z._0-9\-/\\]+) \(0x[0-9a-f]+\)')

            for x in libList:
                m = LIB_RE.fullmatch(x)
                if m is None:
                    continue
                file = m.group('filename')
                libName = os.path.split(file)[1]
                shutil.copyfile(file, os.path.join(self.venvBin, libName))

        log("Copying python executable")
        # Copy the python executable
        newExec = os.path.join(self.venvBin, "python")
        if _IS_WINDOWS:
            newExec += ".exe"
            python_exec = os.path.join(sysconfig.get_config_var("installed_base"), "python.exe")
        shutil.copyfile(python_exec, newExec)
        # Set permissions
        os.chmod(newExec, 0o755)

        log("Copying stdlib")
        # Copy the stdlib
        globalStdlib = sysconfig.get_path('stdlib')

        if _IS_WINDOWS:
            privateStdLib = os.path.join(self._venvDir, "stdlib", "Lib")
        else:
            privateStdLib = os.path.join(self._venvDir, "stdlib", "lib", _PY_VERSION)

        shutil.copytree(globalStdlib, privateStdLib, ignore=shutil.ignore_patterns(*self._config.stdlib_copy_block))

        log("Cleaning environment")
        if _IS_WINDOWS:
            packageDir = os.path.join(self._venvDir, "Lib", "site-packages")
        else:
            packageDir = os.path.join(self._venvDir, "lib", _PY_VERSION, "site-packages")

        for xxx in glob.glob(os.path.join(packageDir, "*.dist-info")):
            shutil.rmtree(xxx)

        def keepCache(filename: str):
            folder, fname = os.path.split(filename)
            fname = os.path.splitext(fname)[0]
            cache = os.path.join(folder, "__pycache__", fname + "*.pyc")
            try:
                cacheFile = glob.glob(cache)[0]
            except IndexError:
                return
            # remove the original file
            os.remove(filename)
            # rename the cached file
            shutil.move(cacheFile, os.path.join(folder, fname + ".pyc"))

        for xxx in glob.glob(os.path.join(packageDir, "*/**.py"), recursive=True):
            keepCache(xxx)

        stdlibCacheBlacklist = ["encodings"]
        BL_RE = re.compile("|".join(stdlibCacheBlacklist))

        for xxx in glob.glob(os.path.join(privateStdLib, "*/**.py"), recursive=True):
            if BL_RE.search(xxx) is not None:
                continue
            keepCache(xxx)

        shutil.copy(os.path.join(_TEMPLATE_DIR, "diamondpack-license.txt"), self._outputDir)

        log("Success - Virtual Environment")

    def _get_cmd(self, script: DPScript) -> str:
        if script.entry is not None:
            return f'-c "from {script.path} import {script.entry}; exit({script.entry}())"'
        else:
            return f'-m {script.path}'

    def _make_script(self, script: DPScript):

        cmd = self._get_cmd(script)

        if _IS_WINDOWS:
            extension = ".bat"
        else:
            extension = ".sh"

        template = "app" + extension
        outfile = os.path.join(self._outputDir, script.name + extension)

        replace = {
            _CMD_REPLACE: cmd,
            _PY_REPLACE: _PY_VERSION
        }

        _do_replace(template, outfile, replace)

        if not _IS_WINDOWS:
            os.chmod(outfile, 0o755)

        log(f'Success - {script.name}')

    def _make_exec(self, script: DPScript):

        cmd = self._get_cmd(script)
        # Escape quotes
        cmd = re.sub(r'"', '\\"', cmd)

        cmakeBuild = os.path.join(self._buildDir, "dp-cmake-build")
        cmakeSrc = os.path.join(self._buildDir, "dp-app-src-dir")
        os.makedirs(cmakeSrc, exist_ok=True)

        template = 'app.cpp'
        outfile = os.path.join(cmakeSrc, f'app.cpp')

        replace = {
            _CMD_REPLACE: cmd,
            _PY_REPLACE: _PY_VERSION
        }

        _do_replace(template, outfile, replace)

        shutil.copy(os.path.join(_TEMPLATE_DIR, "CMakeLists.txt"), cmakeSrc)

        configureParams = ["cmake", "-S", cmakeSrc, "-B", cmakeBuild, f"-DEXEC_NAME={script.name}"]

        buildParams = ["cmake", "--build", cmakeBuild]

        if _IS_WINDOWS:
            buildParams.append("--config=Release")
        else:
            configureParams.append("-DCMAKE_BUILD_TYPE=Release")

        log(f"Building executable - {script.name}")

        log("Configuring CMake")
        ret = execute(configureParams)
        if ret != 0:
            raise RuntimeError(f"Unable to configure cmake: Return code ({ret})")

        log("Building app")
        ret = execute(buildParams)
        if ret != 0:
            raise RuntimeError(f"Unable to compile application: Return code ({ret})")

        log(f"Copying executable - {script.name}")

        if _IS_WINDOWS:
            execName = f'{script.name}.exe'
            execPath = os.path.join(cmakeBuild, "Release", execName)
        else:
            execName = script.name
            execPath = os.path.join(cmakeBuild, execName)

        if not os.path.isfile(execPath):
            raise RuntimeError(f"Cannot find built executable: {execPath}")

        shutil.copy(execPath, os.path.join(self._outputDir, execName))

        log(f'Success - {script.name}')
