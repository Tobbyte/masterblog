"""Configuration file for the Masterblog app."""
from pathlib import Path

db_file_name = "database.json"
uid_file_name = "uid"

uid_file_path = Path("data/" + uid_file_name)
db_file_path = Path("data/" + db_file_name)
