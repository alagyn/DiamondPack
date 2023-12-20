# Packaging
import sys
import os
import shutil
import subprocess as sp
from typing import Optional, List, Dict
import glob
import re
import sysconfig

from diamondpack.dpconfig import DPScript

IS_WINDOWS = sys.platform == 'win32'


def build_env(build_dir: str, wheels: List[str]):
    """
    Creates a virtual env and optionally installs requirements

    :param build_dir: Output build directory
    :param wheels: A list of wheels to install into the venv
    """

    python_exec = sys.executable

    venvDir = os.path.join(build_dir, 'venv')

    if os.path.exists(venvDir):
        shutil.rmtree(venvDir)

    sp.run([python_exec, '-m', 'venv', venvDir, '--copies'])

    if IS_WINDOWS:
        venvBin = os.path.join(venvDir, "Scripts")
    else:
        venvBin = os.path.join(venvDir, "bin")

    venvExec = os.path.join(venvBin, "python")

    if len(wheels) > 0:
        print("Installing wheels")
        args = [
            venvExec,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--force-reinstall",
        ]
        args.extend(wheels)
        sp.run(args)

    venvCfgFile = os.path.join(venvDir, "pyvenv.cfg")
    os.remove(venvCfgFile)

    # remove activate scripts
    for f in glob.glob(os.path.join(venvBin, "activate*")):
        os.remove(f)
    for f in glob.glob(os.path.join(venvBin, "Activate*")):
        os.remove(f)
    for f in glob.glob(os.path.join(venvBin, "deactivate*")):
        os.remove(f)
    for f in glob.glob(os.path.join(venvBin, "Deactivate*")):
        os.remove(f)
    for f in glob.glob(os.path.join(venvBin, "pip*")):
        os.remove(f)
    for f in glob.glob(os.path.join(venvBin, "python*")):
        os.remove(f)

    if IS_WINDOWS:
        # TODO
        pass
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
            shutil.copyfile(file, os.path.join(venvBin, libName))

    # Copy the python executable
    newExec = os.path.join(venvBin, "python")
    if isWindows():
        newExec += ".exe"
        python_exec = os.path.join(sysconfig.get_config_var("installed_base"), "python.exe")
    shutil.copyfile(python_exec, newExec)
    # Set permissions
    os.chmod(newExec, 0o755)
    
    # Copy the stdlib
    stdlibDir = sysconfig.get_path('stdlib')
    if isWindows():
        shutil.copytree(stdlibDir, os.path.join(
            venvDir, "stdlib", "Lib"
        ))
    else:
        shutil.copytree(stdlibDir, os.path.join(
            venvDir,
            "stdlib",
            "lib",
            _get_py_version(),
        ))


APP_REPLACE = '@@SCRIPT@@'
PY_REPLACE = '@@PYTHON@@'

PACKAGE_DIR = os.path.split(__file__)[0]
TEMPLATE_DIR = os.path.join(PACKAGE_DIR, "app-templates")

REPLACE_RE = re.compile("@@[A-Z]+@@")


def _do_replace(template: str, outfile: str, replacements: Dict[str, str]) -> None:
    with open(outfile, mode='w') as outF, open(template, mode='r') as inF:
        for line in inF:
            line = REPLACE_RE.sub(lambda x: replacements[x.group(0)], line)
            outF.write(line)


def _get_py_version() -> str:
    return f'python{sys.version_info.major}.{sys.version_info.minor}'


def make_script(output_dir: str, script: DPScript):
    if IS_WINDOWS:
        name = f'{script.name}.bat'
        template = os.path.join(TEMPLATE_DIR, 'app.bat')
    else:
        name = f'{script.name}.sh'
        template = os.path.join(TEMPLATE_DIR, 'app.sh')

    outfile = os.path.join(output_dir, name)

    replace = {
        APP_REPLACE: target,
        PY_REPLACE: _get_py_version()
    }

    _do_replace(template, outfile, replace)

    if not IS_WINDOWS:
        os.chmod(outfile, 0o755)


def make_exec(build_dir: str, output_dir: str, script: DPScript):

    cmakeBuild = os.path.join(build_dir, "cmake-build")
    cmakeSrc = os.path.join(build_dir, "app-src-dir")
    os.makedirs(cmakeSrc, exist_ok=True)

    template = os.path.join(TEMPLATE_DIR, 'app.cpp')
    outfile = os.path.join(cmakeSrc, f'app.cpp')

    replace = {
        APP_REPLACE: target,
        PY_REPLACE: _get_py_version()
    }

    _do_replace(template, outfile, replace)

    shutil.copy(os.path.join(TEMPLATE_DIR, "CMakeLists.txt"), cmakeSrc)

    configureParams = [
        "cmake", "-S", cmakeSrc, "-B", cmakeBuild, f"-DEXEC_NAME={name}"
    ]

    buildParams = [
        "cmake", "--build", cmakeBuild
    ]

    if isWindows():
        buildParams.append("--config=Release")
    else:
        configureParams.append("-DCMAKE_BUILD_TYPE=Release")

    print("------------- Building executable -------------")

    sp.run(configureParams)
    sp.run(buildParams)

    print("------------- Copying executable -------------")

    if IS_WINDOWS:
        execName = f'{name}.exe'
        execPath = os.path.join(cmakeBuild, "Release", execName)
    else:
        execName = name
        execPath = os.path.join(cmakeBuild, execName)

    if not os.path.isfile(execPath):
        raise RuntimeError(f"Cannot find built executable: {execPath}")

    shutil.copy(execPath, os.path.join(output_dir, execName))
