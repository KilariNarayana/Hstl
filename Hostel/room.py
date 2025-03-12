from data_handler import read_data, write_data


class Room:
    def __init__(self, room_number, capacity):
        self.room_number = room_number
        self.capacity = capacity

    @classmethod
    def get_all_rooms(cls):
        _, rooms = read_data()
        for room in rooms:
            if 'Occupied Beds' not in room:
                room['Occupied Beds'] = 0
        return rooms

    @classmethod
    def add_room(cls, room_data):
        members, rooms = read_data()
        if 'Room Number' not in room_data or 'Capacity' not in room_data:
            raise ValueError("Room data must include 'Room Number' and 'Capacity'.")

        if any(room['Room Number'] == room_data['Room Number'] for room in rooms):
            raise ValueError(f"Room {room_data['Room Number']} already exists.")

        room_data.setdefault('Occupied Beds', 0)
        room_data.setdefault('Floor', 0)
        rooms.append(room_data)
        write_data(members, rooms)

    @staticmethod
    def delete_room(room_number):
        # Read data
        members, rooms = read_data()

        # Filter out the room to be deleted
        update_rooms = [room for room in rooms if str(room['Room Number']) != str(room_number)]
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
            if room['Room Number'] == room_number:
                room['Capacity'] = capacity
                room['Floor'] = floor
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
            else:
                return False

    @staticmethod
    def modify_room(room_number,updated_occupied):
        members, rooms = read_data()
        for room in rooms:
            if room['Room Number'] == room_number:
                room['Occupied Beds'] = updated_occupied
                break
        else:
            raise ValueError(f"Room {room_number} not found.")
        write_data(members, rooms)
        


    @classmethod
    def get_floor_wise_summary(cls):
        summary = {}
        for room in cls.get_all_rooms():
            if 'Floor' not in room:
                print(f"Skipping invalid room data: {room}")
                continue

            floor = room['Floor']
            if floor not in summary:
                summary[floor] = {'Total Beds': 0, 'Occupied Beds': 0, 'Available Beds': 0}

            summary[floor]['Total Beds'] += room.get('Capacity', 0)
            summary[floor]['Occupied Beds'] += room.get('Occupied Beds', 0)
            summary[floor]['Available Beds'] += room.get('Capacity', 0) - room.get('Occupied Beds', 0)

        return summary

    @staticmethod
    def get_bed_count():
        _, rooms = read_data()
        sum_rm = 0
        sum_ob = 0
        for room in rooms:
            sum_rm += room.get('Capacity', 0)
            sum_ob += room.get('Occupied Beds', 0)

        sum_ab = sum_rm - sum_ob
        return sum_rm,sum_ob,sum_ab

    @staticmethod
    def get_room_by_number(room_number):
        return next(
            (room for room in Room.get_all_rooms() if room['Room Number'] == room_number),
            None
        )
