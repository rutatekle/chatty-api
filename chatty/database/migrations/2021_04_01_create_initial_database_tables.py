import os
from chatty.database.chatty_db import ChattyDatabase

current_dir = os.getcwd()
full_file = f"{current_dir}/../../data/restaurant.db"
conn = ChattyDatabase.create_connection(full_file)
chatty_database = ChattyDatabase(conn)
chatty_database.create_initial_tables()
chatty_database.populate_seed_data()
