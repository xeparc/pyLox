"""Entry point."""
import sys

from src.eval import repl, run


USAGE_MSG = """\
Usage:
    jlox [ <FILENAME> ]
"""

if __name__ == '__main__':
    nargs = len(sys.argv)
    match nargs:
        case 1:
            repl()
        case 2:
            with open(sys.argv[1]) as f:
                content = f.read()
                run(content)
        case _:
            print(USAGE_MSG)
            exit(1)
