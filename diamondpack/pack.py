# Packaging
import sys
import os
import shutil
import subprocess as sp
from typing import List, Dict
import glob
import re
import sysconfig

from diamondpack.config import App, PackConfig, DPMode
from diamondpack.log import log

_IS_WINDOWS = sys.platform == 'win32'

_CMD_REPLACE = '@@COMMAND@@'
_PY_REPLACE = '@@PYTHON@@'

_PACKAGE_DIR = os.path.split(__file__)[0]
_TEMPLATE_DIR = os.path.join(_PACKAGE_DIR, "app-templates")

_REPLACE_RE = re.compile("@@[A-Z]+@@")

_PY_VERSION = f'python{sys.version_info.major}.{sys.version_info.minor}'


def _do_replace(template: str, outfile: str, replacements: Dict[str, str]) -> None:
    """
    Copy the contents of the template to the output path replacing values according to the map
    :param template: The template file path
    :param outfile: The output file path
    :param replacements: Dict of replacement values like @@KEY@@: "value"
    """
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


LIB_RE = re.compile(r'[a-zA-Z._0-9/\-+]+ => (?P<filename>[a-zA-Z._0-9\-/\\]+) \(0x[0-9a-f]+\)')


def _copy_linux_required_libs(target: str, outDir: str):
    out = sp.run(["ldd", target], capture_output=True)
    libStr = out.stdout.decode()
    libList = [x.strip() for x in libStr.split("\n")]
    for x in libList:
        m = LIB_RE.fullmatch(x)
        if m is None:
            continue
        file = m.group('filename')
        libName = os.path.split(file)[1]
        shutil.copyfile(file, os.path.join(outDir, libName))


class DiamondPacker:

    def __init__(self, config: PackConfig) -> None:
        self._config = config
        self._buildDir = config.build_dir
        self._outputDir = os.path.join("dist", config.name)
        self._venvDir = os.path.join(self._outputDir, "venv")
        if _IS_WINDOWS:
            self._venvBin = os.path.join(self._venvDir, "Scripts")
            self._venvLib = os.path.join(self._venvDir, "Lib")
        else:
            self._venvBin = os.path.join(self._venvDir, "bin")
            self._venvLib = os.path.join(self._venvDir, "lib", _PY_VERSION)

    def pack(self):
        """
        Main entry point for packing
        """
        log(f"Building Virtual Environment")
        self._build_env()

        for script in self._config.scripts:
            log(f"Generating app - {script.name}")
            if self._config.mode == DPMode.APP:
                self._make_exec(script)
            else:
                self._make_script(script)

        self._copy_data()

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

        venvExec = os.path.join(self._venvBin, "python")

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
            for f in glob.glob(os.path.join(self._venvBin, xxx)):
                os.remove(f)

        # Copy required libraries
        log("Copying required libraries")
        if _IS_WINDOWS:
            libpath = sysconfig.get_config_var("installed_base")
            for file in glob.glob(os.path.join(libpath, "*.dll")):
                fname = os.path.split(file)[1]
                shutil.copyfile(file, os.path.join(self._venvLib, fname))
            otherDLLs = os.path.join(libpath, 'DLLs')
            for file in glob.glob(os.path.join(otherDLLs, "*.dll")):
                fname = os.path.split(file)[1]
                shutil.copyfile(file, os.path.join(self._venvLib, fname))
            for file in glob.glob(os.path.join(otherDLLs, "*.pyd")):
                fname = os.path.split(file)[1]
                shutil.copyfile(file, os.path.join(self._venvLib, fname))
            if self._config.include_tk:
                shutil.copytree(os.path.join(libpath, "tcl", "tcl8.6"), os.path.join(self._venvDir, "Lib", "tcl8.6"))
                shutil.copytree(os.path.join(libpath, "tcl", "tk8.6"), os.path.join(self._venvDir, "Lib", "tk8.6"))
        else:
            _copy_linux_required_libs(python_exec, self._venvBin)

            if self._config.include_tk:
                _copy_linux_required_libs("/usr/lib/libtk8.6.so", self._venvBin)

            if self._config.include_tk:
                shutil.copy("/usr/lib/libtk8.6.so", os.path.join(self._venvBin, "libtk8.6.so"))
                shutil.copytree("/usr/lib/tk8.6", os.path.join(self._venvDir, 'lib', "tk8.6"))

                shutil.copy("/usr/lib/libtcl8.6.so", os.path.join(self._venvBin, "libtcl8.6.so"))
                shutil.copytree("/usr/lib/tcl8.6", os.path.join(self._venvDir, 'lib', "tcl8.6"))

        log("Copying python executable")
        # Copy the python executable
        newExec = os.path.join(self._venvBin, "python")
        if _IS_WINDOWS:
            newExec += ".exe"
            python_exec = os.path.join(sysconfig.get_config_var("installed_base"), "python.exe")
        shutil.copyfile(python_exec, newExec)
        # Set permissions
        os.chmod(newExec, 0o755)

        log("Copying stdlib")
        # Copy the stdlib
        globalStdlib = sysconfig.get_path('stdlib')

        shutil.copytree(
            globalStdlib,
            self._venvLib,
            ignore=shutil.ignore_patterns(*self._config.stdlib_copy_block),
            dirs_exist_ok=True
        )

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

        if len(self._config.cache_block) > 0:
            BL_RE = re.compile("|".join(self._config.cache_block))
        else:
            BL_RE = None

        for xxx in glob.glob(os.path.join(packageDir, "*/**.py"), recursive=True):
            if BL_RE is not None and BL_RE.search(xxx) is not None:
                continue
            keepCache(xxx)

        stdlibCacheBlacklist = ["encodings"]
        BL_RE = re.compile("|".join(stdlibCacheBlacklist))

        for xxx in glob.glob(os.path.join(self._venvLib, "*/**.py"), recursive=True):
            if BL_RE.search(xxx) is not None:
                continue
            keepCache(xxx)

        shutil.copy(os.path.join(_TEMPLATE_DIR, "diamondpack-license.txt"), self._outputDir)

        log("Success - Virtual Environment")

    def _get_cmd(self, app: App) -> str:
        """
        Returns the appropriate python cmd arguments depending on the app's entry point
        :param app: The app
        :return: The command string
        """
        if app.entry is not None:
            # If the app has an entry point defined, run python in "command" mode
            # import the func from the specified module, and execute it
            return f'-c "from {app.path} import {app.entry}; exit({app.entry}())"'
        else:
            # else just run the script as a module
            return f'-m {app.path}'

    def _make_script(self, app: App):
        """
        Generate a .sh or .bat script for the given app
        :param app: The app
        :return: None
        """
        cmd = self._get_cmd(app)

        # Select script extension
        if _IS_WINDOWS:
            extension = ".bat"
        else:
            extension = ".sh"

        # generate filenames
        template = "app" + extension
        outfile = os.path.join(self._outputDir, app.name + extension)

        # generate replacements
        replace = {
            _CMD_REPLACE: cmd,
            _PY_REPLACE: _PY_VERSION
        }

        _do_replace(template, outfile, replace)

        # chmod
        if not _IS_WINDOWS:
            os.chmod(outfile, 0o755)

        log(f'Success - {app.name}')

    def _make_exec(self, app: App):
        """
        Generate an executable for the given app
        :param app: The app
        :return: None
        """

        cmd = self._get_cmd(app)
        # Escape quotes
        cmd = re.sub(r'"', '\\"', cmd)

        # setup cmake dirs
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

        # Copy the build config
        shutil.copy(os.path.join(_TEMPLATE_DIR, "CMakeLists.txt"), cmakeSrc)

        configureParams = ["cmake", "-S", cmakeSrc, "-B", cmakeBuild, f"-DEXEC_NAME={app.name}"]

        buildParams = ["cmake", "--build", cmakeBuild]

        if _IS_WINDOWS:
            buildParams.append("--config=Release")
        else:
            configureParams.append("-DCMAKE_BUILD_TYPE=Release")

        if self._config.debug_logs:
            configureParams.append("-DDEBUG_LOGS=ON")

        log(f"Building executable - {app.name}")

        log("Configuring CMake")
        ret = execute(configureParams)
        if ret != 0:
            raise RuntimeError(f"Unable to configure cmake: Return code ({ret})")

        log("Building app")
        ret = execute(buildParams)
        if ret != 0:
            raise RuntimeError(f"Unable to compile application: Return code ({ret})")

        log(f"Copying executable - {app.name}")

        if _IS_WINDOWS:
            execName = f'{app.name}.exe'
            execPath = os.path.join(cmakeBuild, "Release", execName)
        else:
            execName = app.name
            execPath = os.path.join(cmakeBuild, execName)

        if not os.path.isfile(execPath):
            raise RuntimeError(f"Cannot find built executable: {execPath}")

        shutil.copy(execPath, os.path.join(self._outputDir, execName))

        if not _IS_WINDOWS:
            #_copy_linux_required_libs(execPath, self._outputDir)
            pass

        log(f'Success - {app.name}')

    def _copy_data(self):
        if len(self._config.data_globs) == 0:
            return
        log("Copying Data")
        print("  \u250C")
        for globPath, dest in self._config.data_globs:
            outDir = os.path.join(self._outputDir, dest)
            if not os.path.exists(outDir):
                os.makedirs(outDir, exist_ok=True)
            for f in glob.iglob(globPath):
                if not os.path.isfile(f):
                    continue
                print(f"  \u2502 {f} -> {outDir}\\{os.path.basename(f)}")
                shutil.copy(f, outDir)
        print("  \u2514")
        log("Copying Data - Done")
