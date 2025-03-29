from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date, Numeric, Text, ForeignKey
import urllib.parse
from datetime import date
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_SCHEMA = os.getenv('DB_SCHEMA')

logging.basicConfig(level=logging.ERROR)

# URL-encode the password
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

# Construct the DATABASE_URI
DATABASE_URI = f'postgresql://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}'

engine = create_engine(DATABASE_URI)
metadata = MetaData(schema=DB_SCHEMA)

rooms_table = Table('rooms', metadata,
                    Column('room_number', Integer, primary_key=True),
                    Column('capacity', Integer, nullable=False),
                    Column('floor', Integer, nullable=False),
                    Column('occupied_beds', Integer, default=0))

members_table = Table('members', metadata,
                      Column('member_id', String(50), primary_key=True),
                      Column('name', String(255), nullable=False),
                      Column('phone_number', String(20)),
                      Column('age', Integer),
                      Column('identity_number', String(50)),
                      Column('joining_date', Date),
                      Column('exit_date', Date),
                      Column('father_name', String(255)),
                      Column('father_number', String(20)),
                      Column('address', Text),
                      Column('office_address', Text),
                      Column('room_number', Integer, ForeignKey(f'{DB_SCHEMA}.rooms.room_number')),
                      Column('floor_number', Integer),
                      Column('room_type', String(50)),
                      Column('bed_number', Integer),
                      Column('fee_amount', Numeric(10, 2)),
                      Column('advance_amount', Numeric(10, 2)),
                      Column('identity_document_path', Text),
                      Column('photo_id_path', Text))

fee_details_table = Table('fee_details', metadata,
                          Column('fee_id', String(50), primary_key=True),
                          Column('member_id', String(50), ForeignKey(f'{DB_SCHEMA}.members.member_id'), nullable=False),
                          Column('name', String(100), nullable=False),
                          Column('room_number', Integer, ForeignKey(f'{DB_SCHEMA}.rooms.room_number'), nullable=False),
                          Column('fee_amount', Float, nullable=False),
                          Column('due_date', Date, nullable=False),
                          Column('payment_paid_amount', Float, default=0),
                          Column('advance_paid_amount', Float, default=0),
                          Column('balance_payment', Float, nullable=False),
                          Column('fee_paid_status', String(1), nullable=False),
                          Column('advance_paid_status', String(1), nullable=False),
                          Column('previous_month_balance', Float, default=0),
                          Column('amount_paid_date', Date, nullable=True),
                          Column('created_at', Date, default=date.today),
                          Column('updated_at', Date, default=date.today))

metadata.create_all(engine)


def create_tables_if_not_exists():
    """Ensure tables exist in the database."""
    metadata.create_all(engine)


def read_data():
    """Load members and rooms data from the database."""
    try:
        conn = engine.connect()
        members = conn.execute(members_table.select()).fetchall()
        rooms = conn.execute(rooms_table.select()).fetchall()
        conn.close()

        # Convert tuples to dictionaries
        members_data = [dict(row._mapping) for row in members]
        rooms_data = [dict(row._mapping) for row in rooms]
    except Exception as e:
        print(f"Error reading data: {e}")
        create_tables_if_not_exists()
        members_data, rooms_data = [], []
    return members_data, rooms_data


def write_data(members, rooms):
    """Write updated members and rooms data back to the database."""
    try:
        conn = engine.connect()
        trans = conn.begin()

        # Insert or update rooms data
        for room in rooms:
            existing_room = conn.execute(rooms_table.select().where(rooms_table.c.room_number == room['room_number'])).fetchone()
            if existing_room:
                conn.execute(rooms_table.update().where(rooms_table.c.room_number == room['room_number']).values(room))
            else:
                conn.execute(rooms_table.insert(), room)

        # Insert or update members data
        for member in members:
            existing_member = conn.execute(members_table.select().where(members_table.c.member_id == member['member_id'])).fetchone()
            if existing_member:
                conn.execute(members_table.update().where(members_table.c.member_id == member['member_id']).values(member))
            else:
                conn.execute(members_table.insert(), member)

        trans.commit()
        conn.close()
    except Exception as e:
        print(f"Error writing data: {e}")
        trans.rollback()


if __name__ == "__main__":
    members, rooms = read_data()
   # print(members)
    #print(rooms)
  #  print(read_data())