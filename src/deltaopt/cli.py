import argparse
import contextlib
import json
import sys

from .demo import run
from .evaluation import evaluate


def main():
    parser = argparse.ArgumentParser(description="DeltaOpt offline research prototype")
    parser.add_argument("command", choices=["demo", "evaluate", "semantic-demo"])
    parser.add_argument("--ontology", help="Local Protégé Turtle or RDF/XML ontology")
    parser.add_argument("--shapes", help="Local SHACL Turtle or RDF/XML file")
    parser.add_argument("--output", help="Empty directory for the Protégé/Semantica bundle")
    args = parser.parse_args()
    if args.command == "semantic-demo":
        from .integration_demo import run as integrate
        with contextlib.redirect_stdout(sys.stderr):
            result = integrate(args.ontology, args.shapes, args.output)
    else:
        if args.ontology or args.shapes or args.output:
            parser.error("ontology, shapes and output options require semantic-demo")
        result = run() if args.command == "demo" else evaluate()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
