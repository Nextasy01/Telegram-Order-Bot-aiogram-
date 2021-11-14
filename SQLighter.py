import sqlite3

class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_users(self):
        with self.connection:
            return self.cursor.execute('SELECT user_id FROM users').fetchall()

    def get_orders(self, user_id, tablename):
        with self.connection:
            return self.cursor.execute('SELECT name, sum(' + tablename +'.price) as order_price, count(order_id) as order_count '
                                       'FROM ' + tablename + ' JOIN cart '
                                       'WHERE user_id=? AND '+ tablename +'.ID = cart.order_id AND cart.category=? GROUP BY '+ tablename +'.name HAVING order_count >= 1', (user_id,tablename))

    def get_total_price(self, user_id, tablename):
        with self.connection:
            return self.cursor.execute('SELECT sum(price) as total_price FROM ' + tablename +
                                       ' JOIN cart WHERE ' + tablename +'.ID = cart.order_id AND user_id=? AND category=?', (user_id, tablename,))

    # def clear_order(self, name, user_id):

    def clear_all_orders(self, user_id):
        with self.connection:
            return self.cursor.execute('DELETE FROM cart WHERE user_id=?', (user_id,))

    def insert_product(self, tablename, name, price, pic):
        with self.connection:
            return self.cursor.execute('INSERT INTO ' + tablename + '(name, pic, price) VALUES(?,?,?)', (name, pic, price,))

    def update_product_name(self, tablename, ID, name):
        with self.connection:
            return self.cursor.execute('UPDATE ' + tablename + ' SET name=? WHERE id=?', (name, ID,))

    def update_product_price(self, tablename, ID, price):
        with self.connection:
            return self.cursor.execute('UPDATE ' + tablename + ' SET price=? WHERE id=?', (price, ID,))

    def update_product_pic(self, tablename, ID, pic):
        with self.connection:
            return self.cursor.execute('UPDATE ' + tablename + ' SET pic=? WHERE id=?', (pic, ID,))

    def delete_product(self, tablename, ID):
        with self.connection:
            return self.cursor.execute('DELETE FROM ' + tablename + ' WHERE id=?', (ID,))

    # def get_curr_state(self, user_id):d
    #     with self.connection:
    #         return self.cursor.execute('SELECT curr_state FROM users WHERE user_id=?', (user_id,)).fetchall()
    #
    # def get_prev_state(self, user_id):
    #     with self.connection:
    #         return self.cursor.execute('SELECT prev_state FROM users WHERE user_id=?', (user_id,)).fetchall()
    #
    # def update_state(self, user_id, prev_state, curr_state):
    #     with self.connection:
    #         return self.cursor.execute('UPDATE users SET prev_state=?, curr_state=? WHERE user_id=?', (prev_state, curr_state, user_id))

    def add_new_user(self, user_id, state):
        with self.connection:
            return self.cursor.execute('INSERT INTO users(user_id, curr_state) VALUES(?,?)', (user_id, state,))

    def add_new_order(self, user_id, order_id, tablename):
        with self.connection:
            return self.cursor.execute('INSERT or IGNORE INTO cart(user_id, order_id, category) VALUES(?,?,?)', (user_id, order_id, tablename,))

    def get_id_from_table(self, tablename):
        with self.connection:
            return self.cursor.execute('SELECT id FROM ' + tablename).fetchall()

    def get_pics_from_table(self, tablename):
        with self.connection:
            return self.cursor.execute('SELECT pic FROM ' + tablename).fetchall()

    def get_names_from_table(self, tablename):
        with self.connection:
            return self.cursor.execute('SELECT name FROM ' + tablename).fetchall()

    def get_price_from_table(self, tablename):
        with self.connection:
            return self.cursor.execute('SELECT price FROM ' + tablename).fetchall()

    def get_name(self, tablename, ID):
        with self.connection:
            return self.cursor.execute('SELECT name FROM ' + tablename + ' WHERE id=?', (ID,)).fetchall()[0]

    def get_price(self, tablename, ID):
        with self.connection:
            return self.cursor.execute('SELECT price FROM ' + tablename + ' WHERE id=?', (ID,)).fetchall()[0]
