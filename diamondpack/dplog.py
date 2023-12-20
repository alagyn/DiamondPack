import sys

IS_TERMINAL = sys.stdout.isatty()
ERR = "\x1B[91;1m"
OFF = "\x1B[0m"
GRN = "\x1B[92;1m"
DIAM = "\u25c8"


def logErr(msg) -> None:
    if IS_TERMINAL:
        print(f'{ERR}{DIAM} Error: {msg}{OFF}')
    else:
        print(f'{DIAM} Error: {msg}')
    sys.stdout.flush()


def log(msg) -> None:
    if IS_TERMINAL:
        print(f'{GRN}{DIAM} {msg}{OFF}')
    else:
        print(f'{DIAM} {msg}')
    sys.stdout.flush()
