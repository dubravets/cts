from app.core.db import init_db


def main() -> None:
    db_path = init_db()
    print(f"Initialized database at {db_path}")


if __name__ == "__main__":
    main()
