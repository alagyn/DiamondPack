import sys
import colorama

colorama.just_fix_windows_console()

IS_TERMINAL = sys.stdout.isatty()
ERR = "\x1B[91;1m"
OFF = "\x1B[0m"
GRN = "\x1B[92;1m"
DIAM = "\u25C6"

def logErr(msg) -> None:
    if IS_TERMINAL:
        print(f'{ERR}{DIAM} Error: {msg}{OFF}')
    else:
        print(f'{DIAM} Error: {msg}')
    sys.stdout.flush()


def log(*msg: str) -> None:
    txt = " ".join(msg)
    if IS_TERMINAL:
        print(f'{GRN}{DIAM} {txt}{OFF}')
    else:
        print(f'{DIAM} {txt}')
    sys.stdout.flush()
