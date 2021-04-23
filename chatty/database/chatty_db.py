import sqlite3
from sqlite3 import Error
import pandas as pd


class ChattyDatabase:

    def __init__(self, conn):
        self.conn = conn

    @classmethod
    def create_connection(cls, db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)
        return conn

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def create_table(self, create_table_sql):
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def create_initial_tables(self):
        sql_create_customers_table = """ CREATE TABLE IF NOT EXISTS customers (
                                                id integer PRIMARY KEY,
                                                name text NOT NULL,
                                                email text NOT NULL
                                            ); """

        sql_create_orders_table = """ CREATE TABLE IF NOT EXISTS orders (
                                            id integer PRIMARY KEY,
                                            price float,
                                            date text NOT NULL,
                                            customer_id integer NOT NULL,
                                            FOREIGN KEY (customer_id) REFERENCES Customer (id)
                                        );"""

        sql_create_menu_table = """ CREATE TABLE IF NOT EXISTS menu (
                                                id integer PRIMARY KEY,
                                                name FLOAT NOT NULL,
                                                price text NOT NULL,
                                                category text NOT NULL,
                                                picture text NOT NULL
                                            );"""

        sql_create_order_type_table = """ CREATE TABLE IF NOT EXISTS order_type (
                                                id integer PRIMARY KEY,
                                                meal_id integer NOT NULL,
                                                order_id integer NOT NULL,
                                                quantity integer NOT NULL,
                                                FOREIGN KEY (meal_id) REFERENCES Menu (id)
                                                FOREIGN KEY (order_id) REFERENCES Orders (id)
                                            );"""

        sql_create_dining_table = """ CREATE TABLE IF NOT EXISTS tables (
                                                   id integer PRIMARY KEY,
                                                   chair_count integer NOT NULL,
                                                   status bit NOT NULL
                                               );"""

        sql_create_reservation_table = """ CREATE TABLE IF NOT EXISTS reservation (
                                                   id integer PRIMARY KEY,
                                                   customer_id integer NOT NULL,
                                                   table_id integer NOT NULL,
                                                   date text NOT NULL,
                                                   FOREIGN KEY (customer_id) REFERENCES Customers (id)
                                                   FOREIGN KEY (table_id) REFERENCES Tables (id)
                                               );"""

        self.create_table(sql_create_customers_table)
        self.create_table(sql_create_orders_table)
        self.create_table(sql_create_menu_table)
        self.create_table(sql_create_order_type_table)
        self.create_table(sql_create_dining_table)
        self.create_table(sql_create_reservation_table)

    def populate_seed_data(self):
        with self.conn:
            customer = ('abc', 'abc@gmail.com')
            customer_id = self.customer_entry(customer)

            order = (10, '04-15-2021', customer_id)
            order_id = self.order_entry(order)

            menu = ('Pizza', '11.90', 'pizza', 'pizza.jpg')
            menu_id = self.menu_entry(menu)

            #: Add more menu items
            self.menu_entry(('Pasta', '9.99', 'pasta', 'pasta.jpg'))
            self.menu_entry(('Lasagna', '7.99', 'lazagna', 'lazagna.jpg'))
            self.menu_entry(('Rivoli', '8.99', 'rivoli', 'rivoli.jpg'))
            self.menu_entry(('Calzone', '9.99', 'calzone', 'calzon.jpg'))
            self.menu_entry(('Risotto', '9.99', 'risotto', 'risotto.jpg'))


            order_type = (menu_id, order_id, 2)
            self.order_type_entry(order_type)

            table = (6, 1)
            table_id = self.dining_table_entry(table)

            reservation = (customer_id, table_id, '04-15-2021')
            self.reservation_entry(reservation)

    def customer_entry(self, customer):
        sql = ''' INSERT INTO customers (name,email)
                      VALUES(?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, customer)
        self.conn.commit()
        return cur.lastrowid

    def order_entry(self, order):
        sql = ''' INSERT INTO orders (price, date ,customer_id)
                      VALUES(?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, order)
        self.conn.commit()
        return cur.lastrowid

    def menu_entry(self, order):
        sql = ''' INSERT INTO menu (name, price ,category, picture)
                      VALUES(?,?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, order)
        self.conn.commit()
        return cur.lastrowid

    def order_type_entry(self, order_type):
        sql = ''' INSERT INTO order_type (meal_id, order_id, quantity)
                      VALUES(?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, order_type)
        self.conn.commit()
        return cur.lastrowid

    def dining_table_entry(self, dining_table):
        sql = ''' INSERT INTO tables (chair_count, status)
                      VALUES(?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, dining_table)
        self.conn.commit()
        return cur.lastrowid

    def reservation_entry(self, reservation):
        sql = ''' INSERT INTO reservation (customer_id, table_id ,date)
                      VALUES(?,?,?) '''
        cur = self.conn.cursor()
        cur.execute(sql, reservation)
        self.conn.commit()
        return cur.lastrowid

    def retrieve_all_menu(self):
        query = "select name, price, picture from menu"
        cur = self.conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()

        results = []
        for row in rows:
            results.append({'name': row[0], 'price': row[1], 'picture': row[2]})
        return results

    def retrieve_single_menu(self, menu_name):
        query = "select id from menu where name " + menu_name
        df = pd.read_sql_query(query,self.conn)
        # cur = conn.cursor()
        # cur.execute(query)
        # row = cur.fetchone()
        # return row
        return df

    def retrieve_available_tables(self, chair_count):
        database = r"restaurant.db"
        query = "select id from tables chair_count = " + chair_count + " and status = 1"
        df = pd.read_sql_query(query, self.conn)
        # cur = conn.cursor()
        # cur.execute(query)
        # row = cur.fetchone()
        # return row
        return df

    def save_order_db(self, customer_name, customer_email, food, quantity, total, date, time):
        customer_id = self.customer_entry((customer_name, customer_email))
        order_id = self.order_entry((total, str(date) + " at " + str(time), customer_id))
        meal = self.retrieve_single_menu(food)
        meal_id = meal["id"].values
        self.order_type_entry((meal_id, order_id, quantity))

    def save_booking_db(self, customer_name, customer_email, chair_count, date, time):
        customer_id = self.customer_entry((customer_name, customer_email))
        table = self.retrieve_available_tables(chair_count)
        table_id = table["id"].vlaue()
        self.reservation_entry((customer_id, table_id, date + " at " + time))