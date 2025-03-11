class User:
    def __init__(self, telegram_id, username, first_name, last_name, user_address=None, user_phone=None):
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.user_address = user_address
        self.user_phone = user_phone