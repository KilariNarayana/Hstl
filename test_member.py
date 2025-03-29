from member import Member
from room import Room
from datetime import date, timedelta
import random

def generate_room_data(room_number, capacity, floor):
    return {
        'room_number': room_number,
        'capacity': capacity,
        'floor': floor,
        'occupied_beds': 0  # Initialize occupied beds to 0
    }

def generate_member_data(member_id, room_number, capacity):
    room_types = {1: 'Single', 2: '2 Sharing', 3: '3 Sharing', 4: '4 Sharing', 5: '5 Sharing', 6: '6 Sharing'}
    room_type = room_types.get(capacity, 'Unknown')
    
    start_date = date(2023, 1, 1)
    end_date = date.today()
    delta_days = (end_date - start_date).days
    random_joining_date = start_date + timedelta(days=random.randint(0, delta_days))
    random_fee_amount = random.randint(60, 120) * 100  # Fee amount in increments of 100
    
    return {
        'member_id': f'MEMHSTBH{member_id:06}',
        'name': f'Narayana {member_id}',
        'phone_number': f'123456789{member_id % 10}',
        'age': random.randint(18, 60),
        'identity_number': f'ID{member_id:06}',
        'joining_date': random_joining_date,
        'exit_date': '9999-12-31',
        'father_name': f'Father SubbaRao {member_id}',
        'father_number': f'098765432{member_id % 10}',
        'address': f'{member_id} Main St',
        'office_address': f'{member_id} Office St',
        'room_number': room_number,
        'floor_number': (room_number - 1) // 6 + 1,
        'room_type': room_type,
        'bed_number': member_id % 4 + 1,
        'fee_amount': random_fee_amount,
        'advance_amount': 500.00,
        'identity_document_path': None,
        'photo_id_path': None
    }

def generate_room_capacities(total_capacity, num_rooms):
    capacities = [1] * num_rooms  # Start with a minimum capacity of 1 for each room
    remaining_capacity = total_capacity - num_rooms

    while remaining_capacity > 0:
        for i in range(num_rooms):
            if remaining_capacity > 0:
                increment = random.randint(0, min(remaining_capacity, 3))
                capacities[i] += increment
                remaining_capacity -= increment

    random.shuffle(capacities)
    return capacities

def test_add_rooms():
    # Generate and add 30 rooms with different capacities and floors
    num_rooms = 30
    total_capacity = 100
    capacities = generate_room_capacities(total_capacity, num_rooms)
    rooms = []

    for i in range(1, num_rooms + 1):
        capacity = capacities[i - 1]
        room_data = generate_room_data(i, capacity, (i - 1) // 6 + 1)
        rooms.append(room_data)

    try:
        for room in rooms:
            Room.add_room(room)
        print(f"30 rooms added successfully with total capacity of {total_capacity}.")
    except ValueError as e:
        print(f"Error: {e}")

def test_add_members():
    # Generate and add 100 members
    members = []
    rooms = Room.get_all_rooms()
    print("Rooms data read from database:", rooms)  # Debug statement
    if not rooms:
        raise ValueError("No rooms available. Please add rooms first.")
    room_index = 0

    for i in range(1, 101):
        while room_index < len(rooms) and rooms[room_index]['occupied_beds'] >= rooms[room_index]['capacity']:
            room_index += 1
            if room_index >= len(rooms):
                raise ValueError("Not enough room capacity to accommodate all members.")
        
        room_number = rooms[room_index]['room_number']
        capacity = rooms[room_index]['capacity']
        member_data = generate_member_data(i, room_number, capacity)
        members.append(member_data)
        rooms[room_index]['occupied_beds'] += 1

    try:
        for member in members:
            Member.add_member(member)
        print(f"100 members added successfully.")
    except ValueError as e:
        print(f"Error: {e}")

def test_get_all_members():
    # Get all members
    members = Member.get_all_members()
    print("All active members:")
    for member in members:
        print(member)

def test_update_member():
    # Define updated member data
    updated_data = {
        'phone_number': '0987654321',
        'address': '789 New St'
    }

    # Update the member
    try:
        Member.update_member('MEMHSTBH000001', updated_data)
        print("Member updated successfully.")
    except ValueError as e:
        print(f"Error: {e}")

def test_update_exit_date():
    # Update the exit date of a member
    try:
        Member.update_exit_date('MEMHSTBH000001', date(2023, 12, 31))
        print("Exit date updated successfully.")
    except ValueError as e:
        print(f"Error: {e}")

def test_search_member():
    # Search for members by name
    search_results = Member.search_member('name', 'John')
    print("Search results by name:")
    for member in search_results:
        print(member)

    # Search for members by room number
    search_results = Member.search_member('room', 1)
    print("Search results by room number:")
    for member in search_results:
        print(member)

    # Search for members by phone number
    search_results = Member.search_member('phone', '1234567890')
    print("Search results by phone number:")
    for member in search_results:
        print(member)

def test_get_member_by_id():
    # Get member by ID
    try:
        member = Member.get_member_by_id('MEMHSTBH000001')
        print("Member details:")
        print(member)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test adding rooms
    test_add_rooms()

    # Test adding members
    test_add_members()

    # Test getting all members
    test_get_all_members()

    # Test updating a member
    test_update_member()

    # Test updating exit date
    test_update_exit_date()

    # Test searching for members
    test_search_member()

    # Test getting member by ID
    test_get_member_by_id()