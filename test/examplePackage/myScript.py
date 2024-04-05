# Example executable script
import sys
from examplePackage.myModule import add
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument("A", type=int, help="The first arg")
    parser.add_argument("B", type=int, help="The second arg")
    args = parser.parse_args()
    a = args.A
    b = args.B
    print(f"Wow, {a} + {b} =", add(a, b))


if __name__ == '__main__':
    main()
