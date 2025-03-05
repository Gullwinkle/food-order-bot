import sqlite3

db_name = 'db/order_bot.db'

def add_user(telegram_id, username, first_name, last_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)", (telegram_id, username, first_name, last_name,))
    conn.commit()
    conn.close()

def add_user_address(user_id, address):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET user_address = ? WHERE telegram_id = ?", (address, user_id))
    conn.commit()
    conn.close()

      # достаём адрес доставки по id
def get_user_address(user_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT user_address FROM users WHERE telegram_id = ?",(user_id,))
    result = cursor.fetchall()
    conn.close()
    print(f'Результат: {result}')
    return result


def get_restaurants():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, logo FROM restaurants")
    result = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1], "description": row[2], "logo": row[3]} for row in result]


def get_categories(restaurant_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories WHERE restaurant_id = ?", (restaurant_id,))
    result = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1]} for row in result]


def get_dishes(category_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, description, image FROM dishes WHERE category_id = ?", (category_id,))
    result = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1], "price": row[2], "description": row[3], "image": row[4]} for row in result]


def add_to_cart(user_id, dish_id, price, restaurant_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM orders WHERE user_id = ? AND status = 'new'", (user_id,))
    order = cursor.fetchone()

    if order is None:
        cursor.execute("INSERT INTO orders (user_id, restaurant_id, status, total_cost) VALUES (?, ?, 'new', 0)",
                       (user_id, restaurant_id))
        order_id = cursor.lastrowid
    else:
        order_id = order[0]

    cursor.execute("SELECT quantity FROM order_items WHERE order_id = ? AND dish_id = ?", (order_id, dish_id))
    item = cursor.fetchone()

    if item is None:
        cursor.execute(
            "INSERT INTO order_items (order_id, dish_id, quantity, price, total) VALUES (?, ?, 1, ?, ?)",
            (order_id, dish_id, price, price))
        cursor.execute("UPDATE orders SET total_cost = total_cost + ? WHERE id = ?", (price, order_id))
    else:
        new_quantity = item[0] + 1
        new_total = new_quantity * price
        cursor.execute("UPDATE order_items SET quantity = ?, total = ? WHERE order_id = ? AND dish_id = ?",
                       (new_quantity, new_total, order_id, dish_id))
        cursor.execute("UPDATE orders SET total_cost = total_cost + ? WHERE id = ?", (price, order_id))

    conn.commit()
    conn.close()


def get_cart(user_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT dishes.name AS dish_name, quantity, total FROM order_items "
                   "INNER JOIN dishes ON order_items.dish_id = dishes.id "
                   "WHERE order_id IN (SELECT id FROM orders WHERE user_id = ? AND status = 'new')", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return [{"dish_name": row[0], "quantity": row[1], "total": row[2]} for row in result]


def change_order_status(user_id, status):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE user_id = ? AND status = 'new' OR status = 'confirmed'", (status, user_id))
    conn.commit()
    conn.close()


def change_order_payment_method(order_id, payment_method):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET payment_method = ? WHERE id = ? AND status = 'paid' OR status = 'confirmed'", (payment_method, order_id))
    conn.commit()
    conn.close()


def get_user_orders(user_id, ordering='ASC', limit=None):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    # Проверяем, что ordering имеет допустимое значение
    if ordering.upper() not in ('ASC', 'DESC'):
        ordering = 'ASC'  # Значение по умолчанию

    # Формируем SQL-запрос с безопасным добавлением сортировки
    query = f"""
        SELECT id, user_id, restaurant_id, status, total_cost, payment_method, 
               DATE(order_date) AS updated_at 
        FROM orders 
        WHERE user_id = ? AND status != 'new'
        ORDER BY id {ordering}
    """

    # Добавляем LIMIT, если указано значение
    params = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return [{"id": row[0],
             "user_id": row[1],
             "restaurant_id": row[2],
             "status": row[3],
             "total_cost": row[4],
             "payment_method": row[5],
             "updated_at": row[6]}
            for row in result]

def get_user_unrated_orders(user_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT orders.id, name, status, total_cost, DATE(order_date) as updated_at"
                   " FROM orders JOIN restaurants ON orders.restaurant_id = restaurants.id "
                   "WHERE user_id = ? AND status = 'paid'"
                   " ORDER BY updated_at DESC LIMIT 6", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "name": row[1], "status": row[2], "total_cost": row[3], "updated_at": row[4]} for row in result]

def get_current_order_id(user_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM orders WHERE user_id = ? AND status = 'confirmed'", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0]



def add_fb(telegram_id, data_fb, fb_t, fb_r):
    print(data_fb)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO restaurant_reviews (user_id, restaurant_id, order_id, comment, rating) VALUES (?, ?, ?, ?, ?)",
                    (telegram_id, data_fb['restaurant_id'], data_fb['id'], fb_t, fb_r))
    conn.commit()
    conn.close()

def add_rest_rating(user_id, restaurant_id, order_id, rating):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO restaurant_reviews (user_id, restaurant_id, order_id, rating) VALUES (?, ?, ?, ?)",
                    (user_id, restaurant_id, order_id, rating))
    cursor.execute("UPDATE orders SET status = 'rated' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

def get_rest_id(order_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT restaurant_id FROM orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0]

def get_rest_fb(restaurant_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(rating), COUNT(rating) FROM restaurant_reviews WHERE restaurant_id = ?", (restaurant_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_username(telegram_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT first_name FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result
