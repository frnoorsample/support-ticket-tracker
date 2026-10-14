"""App settings, read from environment variables so secrets never live in the code."""
import os

# Where the SQLite database file is stored.
DATABASE_PATH = os.getenv("DATABASE_PATH", "tickets.db")