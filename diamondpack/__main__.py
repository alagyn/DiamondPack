from argparse import ArgumentParser
import os


def main():
    parser = ArgumentParser()
    parser.add_argument('-r', '--req', help="Requirements file")
    parser.add_argument('-b', '--build', help="Build directory", default='build')
    parser.add_argument('--python', help="Python executable to use")
    parser.add_argument("--wheels", nargs="*")
    parser.add_argument("--scripts", nargs="+")
    parser.add_argument("--name", help="Package Name", required=True)
    parser.add_argument('--mode', choices=["script", "app"], default="script")

    args = parser.parse_args()

    if args.scripts is None or len(args.scripts) == 0:
        print("No scripts, why are you even using this?")

    from diamondpack.pack import build_env, make_script, make_exec

    outputdir = os.path.join(args.build, args.name)

    build_env(outputdir, args.python, args.wheels, args.req)

    if args.scripts is not None:
        for script in args.scripts:
            if args.mode == "script":
                make_script(outputdir, script, None)
            else:
                make_exec(args.build, outputdir, script, None)


if __name__ == '__main__':
    main()
