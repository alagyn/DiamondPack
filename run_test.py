from argparse import ArgumentParser
import os
import shutil
import sys
import subprocess as sp

EXAMPLE = "example-1.0.0"
WHEEL = f"dist/{EXAMPLE}-py3-none-any.whl"

HOME = os.path.split(__file__)[0]
IS_WINDOWS = sys.platform == 'win32'


def main():
    parser = ArgumentParser()
    parser.add_argument("run_mode", choices=["cli", "project"])
    parser.add_argument("build_mode", choices=["app", "script"])
    parser.add_argument("--wheel", action="store_true", help="Force rebuilding of the test wheel")

    args = parser.parse_args()

    run_mode = args.run_mode
    build_mode = args.build_mode

    os.chdir(os.path.join(HOME, "test"))

    # Build test wheel
    if args.wheel or not os.path.exists(WHEEL):
        sp.run([sys.executable, "-m", "build", "--wheel"])

    # Delete the existing test
    dist = os.path.join("dist", EXAMPLE)
    if os.path.isdir(dist):
        shutil.rmtree(dist)

    print("Begin Diamond packing:")

    env = os.environ.copy()
    env["PYTHONPATH"] = HOME

    if run_mode == "cli":
        run = sp.run(
            [
                sys.executable,
                "-m",
                "diamondpack",
                "--wheels",
                WHEEL,
                "--scripts",
                "myScript=examplePackage.myScript",
                "--name",
                "example-1.0.0",
                "--mode",
                build_mode
            ],
            env=env
        )
    else:
        run = sp.run([sys.executable, "-m", "diamondpack"], env=env)

    if run.returncode != 0:
        print("Pack Failed: ", run.returncode)
        return

    os.chdir(f"dist/{EXAMPLE}/")

    if build_mode == "script":
        if IS_WINDOWS:
            script = f"myScript.bat"
        else:
            script = f"myScript.sh"
    else:
        if IS_WINDOWS:
            script = f"myScript.exe"
        else:
            script = f"myScript"

    print("Executing Test Script")

    sp.run([script, "1", "4"])


if __name__ == "__main__":
    main()
