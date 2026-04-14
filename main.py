from cli import make_parser

def main(argv: list[str] | None = None) -> None:
    parser = make_parser()
    try:
        args = parser.parse_args(argv)
        args.func(args)
    except ValueError as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()