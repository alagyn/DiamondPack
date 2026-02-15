from argparse import ArgumentParser
import os
import shutil
import sys
import subprocess as sp

EXAMPLE = "example-1.0.0"
WHEEL = f"dist/{EXAMPLE}-py3-none-any.whl"

HOME = os.path.split(__file__)[0]
IS_WINDOWS = sys.platform == 'win32'


def testExec(file, *args) -> bool:
    if IS_WINDOWS:
        exePath = f'{file}.exe'
        batPath = f'{file}.bat'
        if os.path.isfile(exePath):
            script = exePath
        elif os.path.isfile(batPath):
            script = batPath
        else:
            print("Cannot find executable")
            return False
    else:
        exePath = file
        shPath = f'{file}.sh'
        if os.path.isfile(exePath):
            script = f"./{exePath}"
        elif os.path.isfile(shPath):
            script = f"./{shPath}"
        else:
            print("Cannot find executable")
            return False

    ret = sp.call([script, *args])

    return ret != 0


def main():
    parser = ArgumentParser()
    parser.add_argument("--wheel", action="store_true", help="Force rebuilding of the test wheel")

    args = parser.parse_args()

    os.chdir(os.path.join(HOME, "test"))

    # Delete the existing test
    dist = os.path.join("dist", EXAMPLE)
    if os.path.isdir(dist):
        shutil.rmtree(dist)

    print("Begin Diamond packing:")

    env = os.environ.copy()
    env["PYTHONPATH"] = HOME

    run = sp.run([sys.executable, "-m", "diamondpack"], env=env)

    if run.returncode != 0:
        print("Pack Failed: ", run.returncode)
        return

    os.chdir(f"dist/{EXAMPLE}/")

    print("Executing Test Scripts")

    tests = [
        ["myScript", "1", "4"],
        ["gui", "--noRun"],
    ]

    fail = False
    for idx, val in enumerate(tests):
        if testExec(*val):
            print(f"Failed Test {idx}: {val}")
            fail = True
        else:
            print(f"Passed Test {idx}")

    if fail:
        exit(1)


if __name__ == "__main__":
    main()
