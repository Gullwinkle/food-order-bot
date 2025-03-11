from models.user import User
from database.db_connection import DBConnection

class UserRepository:
    def __init__(self, db_name):
        self.db_name = db_name

    def add_user(self, user: User):
        with DBConnection(self.db_name) as cursor:
            cursor.execute(
                "INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (user.telegram_id, user.username, user.first_name, user.last_name)
            )

    def get_user_address(self, user_id):
        with DBConnection(self.db_name) as cursor:
            cursor.execute("SELECT user_address FROM users WHERE telegram_id = ?", (user_id,))
            return cursor.fetchone()

    def add_user_address(self, user_id, address):
        with DBConnection(self.db_name) as cursor:
            cursor.execute("UPDATE users SET user_address = ? WHERE telegram_id = ?", (address, user_id))