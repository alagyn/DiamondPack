from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument('-r', '--req', help="Requirements file")
    parser.add_argument('-s', '--src', help="Source directory", default=',')
    parser.add_argument('-b', '--build', help="Build directory", default='build')
    parser.add_argument('--python', help="Python executable to use")
    parser.add_argument("--wheels", nargs="*")
    parser.add_argument("--scripts", nargs="*")

    args = parser.parse_args()

    from diamondpack.pack import build_env, make_script

    build_env(args.build, args.python, args.wheels, args.req)
    if args.scripts is not None:
        for script in args.scripts:
            make_script(args.build, script, None)


if __name__ == '__main__':
    main()
