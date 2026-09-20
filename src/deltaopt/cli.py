import argparse
import json

from .demo import run
from .evaluation import evaluate


def main():
    parser = argparse.ArgumentParser(description="DeltaOpt offline research prototype")
    parser.add_argument("command", choices=["demo", "evaluate"])
    args = parser.parse_args()
    print(json.dumps(run() if args.command == "demo" else evaluate(), indent=2))


if __name__ == "__main__":
    main()
