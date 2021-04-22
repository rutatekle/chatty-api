import sqlite3
from sqlite3 import Error
import pandas as pd


class ChattyDatabase:

    def create_connection(self,db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)

    def close_connection(self,conn):
        if conn:
            conn.close()

    def create_table(self,conn, create_table_sql):
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def table_creation_query(self, conn):
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

        self.create_table(conn, sql_create_customers_table)
        self.create_table(conn, sql_create_orders_table)
        self.create_table(conn, sql_create_menu_table)
        self.create_table(conn, sql_create_order_type_table)
        self.create_table(conn, sql_create_dining_table)
        self.create_table(conn, sql_create_reservation_table)

    def create_populate_tables(self):
        database = r"restaurant.db"
        conn = self.create_connection(database)
        self.table_creation_query(conn)

        with conn:
            customer = ('abc', 'abc@gmail.com')
            customer_id = self.customer_entry(conn, customer)

            order = (10, '04-15-2021', customer_id)
            order_id = self.order_entry(conn, order)

            menu = ('pizza', '5.00', 'pizza', 'pizza.jpg')
            menu_id = self.menu_entry(conn, menu)

            order_type = (menu_id, order_id, 2)
            self.order_type_entry(conn, order_type)

            table = (6, 1)
            table_id = self.dining_table_entry(conn, table)

            reservation = (customer_id, table_id, '04-15-2021')
            self.reservation_entry(conn, reservation)

    def customer_entry(self, conn, customer):
        sql = ''' INSERT INTO customers (name,email)
                      VALUES(?,?) '''
        cur = conn.cursor()
        cur.execute(sql, customer)
        conn.commit()
        return cur.lastrowid

    def order_entry(self, conn, order):
        sql = ''' INSERT INTO orders (price, date ,customer_id)
                      VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, order)
        conn.commit()
        return cur.lastrowid

    def menu_entry(self, conn, order):
        sql = ''' INSERT INTO menu (name, price ,category, picture)
                      VALUES(?,?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, order)
        conn.commit()
        return cur.lastrowid

    def order_type_entry(self, conn, order_type):
        sql = ''' INSERT INTO order_type (meal_id, order_id, quantity)
                      VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, order_type)
        conn.commit()
        return cur.lastrowid

    def dining_table_entry(self, conn, dining_table):
        sql = ''' INSERT INTO tables (chair_count, status)
                      VALUES(?,?) '''
        cur = conn.cursor()
        cur.execute(sql, dining_table)
        conn.commit()
        return cur.lastrowid

    def reservation_entry(self, conn, reservation):
        sql = ''' INSERT INTO reservation (customer_id, table_id ,date)
                      VALUES(?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, reservation)
        conn.commit()
        return cur.lastrowid

    def retrieve_all_menu(self,conn):
        database = r"restaurant.db"
        conn = self.create_connection(database)
        query = "select * from menu"
        df = pd.read_sql_query(query, conn)
        # cur = conn.cursor()
        # cur.execute(query)
        # row = cur.fetchone()
        # return row
        return df

    def retrieve_single_menu(self,conn, menu_name):
        database = r"restaurant.db"
        conn = self.create_connection(database)
        query = "select id from menu where name " + menu_name
        df = pd.read_sql_query(query,conn)
        # cur = conn.cursor()
        # cur.execute(query)
        # row = cur.fetchone()
        # return row
        return df

    def retrieve_available_tables(self,conn, chair_count):
        database = r"restaurant.db"
        conn = self.create_connection(database)
        query = "select id from tables chair_count = " + chair_count + " and status = 1"
        df = pd.read_sql_query(query, conn)
        # cur = conn.cursor()
        # cur.execute(query)
        # row = cur.fetchone()
        # return row
        return df

    def save_order_db(self, conn, customer_name, customer_email, food, quantity, total, date, time):
        customer_id = self.customer_entry(conn, (customer_name, customer_email))
        order_id = self.order_entry(conn, (total, str(date) + " at " + str(time), customer_id))
        meal = self.retrieve_single_menu(conn, food)
        meal_id = meal["id"].values
        self.order_type_entry(conn, (meal_id, order_id, quantity))

    def save_booking_db(self, conn, customer_name, customer_email, chair_count, date, time):
        customer_id = self.customer_entry(conn, (customer_name, customer_email))
        table = self.retrieve_available_tables(conn, chair_count)
        table_id = table["id"].vlaue()
        self.reservation_entry(conn, (customer_id, table_id, date + " at " + time))