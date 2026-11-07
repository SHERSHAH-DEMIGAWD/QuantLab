"""python -m quantlab.api: fixed loopback bind, no uploaded server paths."""

import argparse

import uvicorn

from .app import create_app


def main():
    parser = argparse.ArgumentParser(description="Run the single-user local QuantLab backend.")
    parser.add_argument("--database", default="data/quantlab.sqlite3", help="Operator-selected SQLite path.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(create_app(args.database), host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
