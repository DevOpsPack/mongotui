import argparse

from mongotui.app import MongoTUI


def main():
    parser = argparse.ArgumentParser(description="MongoTUI - Terminal UI for MongoDB")
    parser.add_argument("--uri", "-u", help="MongoDB connection URI (skips connect screen)")
    args = parser.parse_args()

    app = MongoTUI(uri=args.uri)
    app.run()


if __name__ == "__main__":
    main()
