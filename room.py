from data_handler import read_data, write_data
from member import Member

class Room:
    def __init__(self, room_number, capacity):
        self.room_number = room_number
        self.capacity = capacity

    @classmethod
    def get_all_rooms(cls):
        _, rooms = read_data()
        for room in rooms:
            if 'occupied_beds' not in room:
                room['occupied_beds'] = 0
        return rooms

    @classmethod
    def add_room(cls, room_data):
        members, rooms = read_data()
        print("Rooms data read from database:", room_data)  # Debug print
        if 'room_number' not in room_data or 'capacity' not in room_data:
            raise ValueError("Room data must include 'room_number' and 'capacity'.")

        if any(room['room_number'] == room_data['room_number'] for room in rooms):
            raise ValueError(f"Room {room_data['room_number']} already exists.")

        new_room = {
            'room_number': room_data['room_number'],
            'capacity': room_data['capacity'],
            'floor': room_data.get('floor', 0),
            'occupied_beds': 0
        }
        rooms.append(new_room)
        write_data(members, rooms)
        print("Rooms data after adding new room:", rooms)  # Debug print

    @staticmethod
    def delete_room(room_number):
        # Read data
        members, rooms = read_data()

        # Filter out the room to be deleted
        update_rooms = [room for room in rooms if str(room['room_number']) != str(room_number)]
        update_members = [member for member in members if str(member.get('room_number', '')) != str(room_number)]
        if len(rooms) == len(update_rooms):
            raise ValueError(f"Room {room_number} not found.")

        # Write updated data
        write_data(update_members, update_rooms)

    @staticmethod
    def update_room(room_number, capacity, floor):
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")

        members, rooms = read_data()
        room_found = False
        for room in rooms:
            if room['room_number'] == room_number:
                room['capacity'] = capacity
                room['floor'] = floor
                room_found = True
                break

        if not room_found:
            raise ValueError(f"Room {room_number} not found.")
        write_data(members, rooms)
        
    @staticmethod
    def has_assigned_members(room_number):
        members, _ = read_data()
        for member in members:
            if member.get('room_number') == room_number:
                return True
        return False

    @staticmethod
    def modify_room(room_number, updated_occupied):
        members, rooms = read_data()
        for room in rooms:
            if room['room_number'] == room_number:
                room['occupied_beds'] = updated_occupied
                break
        else:
            raise ValueError(f"Room {room_number} not found.")
        write_data(members, rooms)
        
    @classmethod
    def get_floor_wise_summary(cls):
        summary = {}
        for room in cls.get_all_rooms():
            if 'floor' not in room:
                print(f"Skipping invalid room data: {room}")
                continue

            floor = room['floor']
            if floor not in summary:
                summary[floor] = {'Total Beds': 0, 'Occupied Beds': 0, 'Available Beds': 0}

            summary[floor]['Total Beds'] += room.get('capacity', 0)
            summary[floor]['Occupied Beds'] += room.get('occupied_beds', 0)
            summary[floor]['Available Beds'] += room.get('capacity', 0) - room.get('occupied_beds', 0)

        return summary

    @staticmethod
    def get_bed_count():
        _, rooms = read_data()
        sum_rm = 0
        sum_ob = 0
        for room in rooms:
            sum_rm += room.get('capacity', 0)
            sum_ob += room.get('occupied_beds', 0)

        sum_ab = sum_rm - sum_ob
        return sum_rm, sum_ob, sum_ab

    @staticmethod
    def get_room_by_number(room_number):
        return next(
            (room for room in Room.get_all_rooms() if room['room_number'] == room_number),
            None
        )

    @staticmethod
    def update_occupied_beds(room_number):
        members, rooms = read_data()
        active_members = Member.get_all_members()
        for room in rooms:
            if room['room_number'] == room_number:
                room['occupied_beds'] = sum(1 for member in active_members if member['room_number'] == room_number)
                break
        else:
            raise ValueError(f"Room {room_number} not found.")
        write_data(members, rooms)

    @staticmethod
    def recalculate_all_occupied_beds():
        members, rooms = read_data()
        active_members = Member.get_all_members()
        for room in rooms:
            room['occupied_beds'] = sum(1 for member in active_members if member['room_number'] == room['room_number'])
        write_data(members, rooms)


if __name__ == "__main__":
    # Test inserting a room
    room_data = {
        'room_number': 101,
        'capacity': 4,
        'floor': 1
    }
    try:
        Room.add_room(room_data)
        print(f"Room {room_data['room_number']} added successfully.")
    except ValueError as e:
        print(f"Error: {e}")
 
    #Update room
    #Room.update_room(104, 4, 1)
    print("Room updated successfully.")

    # Test getting all rooms
    rooms = Room.get_all_rooms()
    print("All rooms:")
    for room in rooms:
        print(room)