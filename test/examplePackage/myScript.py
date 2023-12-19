# Example executable script
import sys
from examplePackage.myModule import add


def main():
    a = int(sys.argv[1])
    b = int(sys.argv[2])
    print(f"Wow, {a} + {b} =", add(a, b))


if __name__ == '__main__':
    main()
