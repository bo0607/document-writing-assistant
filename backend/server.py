import argparse

from app.main import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the document writing assistant service.")
    parser.add_argument("--host", default="127.0.0.1", help="Address to listen on.")
    parser.add_argument("--port", default=8000, type=int, help="Port to listen on.")
    args = parser.parse_args()
    run(args.host, args.port)
