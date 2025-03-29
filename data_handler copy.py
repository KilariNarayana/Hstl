import pandas as pd
import os

EXCEL_FILE = 'hostel_data.xlsx'


def create_excel_if_not_exists(members=None, rooms=None):
    """Ensure Excel file exists with proper sheets."""
    try:
        if not os.path.exists(EXCEL_FILE):
            with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
                if not members:
                    members = []
                if not rooms:
                    rooms = []
                pd.DataFrame(members).to_excel(writer, sheet_name='members', index=False)
                pd.DataFrame(rooms).to_excel(writer, sheet_name='Rooms', index=False)
    except Exception as e:
        print(f"Error creating Excel file: {e}")


def read_data():
    """Load members and rooms data from the Excel file."""
    try:
        members = pd.read_excel(EXCEL_FILE, sheet_name='members').to_dict(orient='records')
        rooms = pd.read_excel(EXCEL_FILE, sheet_name='Rooms').to_dict(orient='records')
    except Exception as e:
        print(f"Error reading data: {e}")
        create_excel_if_not_exists()
        members, rooms = [], []
    return members, rooms


def write_data(members, rooms):
    """Write updated members and rooms data back to the Excel file."""
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            pd.DataFrame(members).to_excel(writer, sheet_name='members', index=False)
            pd.DataFrame(rooms).to_excel(writer, sheet_name='Rooms', index=False)
    except Exception as e:
        print(f"Error writing data: {e}")

if __name__ == "__main__":
    members, rooms = read_data()
    print(members)
    print(rooms)