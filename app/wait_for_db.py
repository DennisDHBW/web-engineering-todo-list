import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

DATABASE_URL = "postgresql://user:password@db:5432/todoapp"
engine = create_engine(DATABASE_URL)

while True:
    try:
        with engine.connect() as connection:
            print("Database is ready.")
            break
    except OperationalError:
        print("Waiting for database...")
        time.sleep(2)