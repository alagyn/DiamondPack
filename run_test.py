from argparse import ArgumentParser
import os
import shutil
import sys
import subprocess as sp

WHEEL="test/dist/example-1.0.0-py3-none-any.whl"

HOME=os.path.split(__file__)[0]
IS_WINDOWS = sys.platform == 'win32'

def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=["app", "script"])
    parser.add_argument("--wheel", action="store_true", help="Force rebuilding of the test wheel")

    args = parser.parse_args()

    os.chdir(HOME)

    # Build test wheel
    if args.wheel or not os.path.exists(WHEEL):
        os.chdir("test")
        sp.run([
            sys.executable, "-m", "build", "--wheel"
        ])
        os.chdir(HOME)

    # Delete the existing test
    shutil.rmtree("test-dist")

    print("Diamond packing:")

    run = sp.run(
        [
            sys.executable, "-m", "diamondpack",
            "--build", "test-dist",
            "--wheels", WHEEL,
            "--scripts", "examplePackage.myScript",
            "--name", "example",
            "--mode", args.mode
        ]
    )

    if run.returncode != 0:
        print("Pack Failed: ", run.returncode)
        return

    if args.mode == "script":
        if IS_WINDOWS:
            script = os.path.join(HOME, "test-dist/example/examplePackage.myScript.bat")
        else:
            script = os.path.join(HOME, "test-dist/example/examplePackage.myScript.sh")
    else:
        if IS_WINDOWS:
            script = os.path.join(HOME, "test-dist/example/examplePackage.myScript.exe")
        else:
            script = os.path.join(HOME, "test-dist/example/examplePackage.myScript")
    
    print("Executing Test Script")

    sp.run(
        [script, "1", "4"]
    )







if __name__ == "__main__":
    main()