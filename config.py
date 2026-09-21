"""Configuration file for the Masterblog app."""
from pathlib import Path

db_file_name = "database.json"
uid_file_name = "uid"

UID_FILE_PATH = Path("data/" + uid_file_name)
DB_FILE_PATH = Path("data/" + db_file_name)


ERR_NO_POST_UID = "No previous post_uid found, generate from posts."
ERR_SAVE_POST_UID = "Error saving uid file, abort."
ERR_DB_CORRUPT = "DB file corrupt, abort."
ERR_SAVE_DATA_FAILED = "Saving data failed, abort."
