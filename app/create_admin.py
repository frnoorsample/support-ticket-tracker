import sys

from app.database import get_connection, init_db


def make_admin(username: str) -> None:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
        if cursor.rowcount == 0:
            print(f"No user called '{username}'. Register them first.")
        else:
            print(f"'{username}' is now an admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.create_admin <username>")
        sys.exit(1)
    make_admin(sys.argv[1])