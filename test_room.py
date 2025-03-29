from room import Room

def test_insert_room():
    # Define room data
    room_data = {
        'Room Number': 101,
        'Capacity': 4,
        'Floor': 1
    }

    # Insert the room
    try:
        Room.add_room(room_data)
        print(f"Room {room_data['Room Number']} added successfully.")
    except ValueError as e:
        print(f"Error: {e}")

def test_get_all_rooms():
    # Get all rooms
    rooms = Room.get_all_rooms()
    print("All rooms:")
    for room in rooms:
        print(room)

if __name__ == "__main__":
    # Test inserting a room
    test_insert_room()

    # Test getting all rooms
    test_get_all_rooms()

