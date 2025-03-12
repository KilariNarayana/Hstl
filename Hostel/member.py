import os
from werkzeug.utils import secure_filename
from data_handler import read_data, write_data


class Member:
    PREFIX = "MEMHSTBH"

    def __init__(self, name, phone_number, member_id, **kwargs):
        self.name = name
        self.phone_number = phone_number
        self.member_id = member_id
        self.kwargs = kwargs  # Other dynamic details

    @staticmethod
    def get_all_members():
        members, _ = read_data()
        active_members=[members for members in members if members['exit_date'] == '9999-12-31']
        return active_members

    @staticmethod
    def _allowed_file(filename):
        """
        Checks if a file's extension is allowed.
        """
        allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def generate_member_id():
        members, _ = read_data()  # Read all current members
        if not members:
            # If there are no members, start with MEMHSTBH000001
            return f"{Member.PREFIX}000001"

        # Extract existing IDs, remove PREFIX, and get the numeric part
        existing_ids = [
            int(member.get('member_id','0')[len(Member.PREFIX):])
            for member in members if member.get('member_id', '').startswith(Member.PREFIX)
        ]

        # Find the maximum sequence number and increment it
        next_id = max(existing_ids, default=0) + 1

        # Generate the new ID with padded zeros (up to 6 digits)
        return f"{Member.PREFIX}{str(next_id).zfill(6)}"

    @staticmethod
    def add_member(member_data, identity_document=None, photo_id=None, upload_folder=None):
        """
        Adds a new member to the database. Provides support for uploading an identity document
        and a photo ID if provided.

        :param member_data: Dictionary of member details
        :param identity_document: File object for the identity document
        :param photo_id: File object for the photo ID
        :param upload_folder: Folder path where files will be saved
        """
        members, rooms = read_data()

        # Generate a new member ID
        member_id = Member.generate_member_id()
        member_data['member_id'] = member_id  # Use consistent key for member ID

        # Handle identity document upload if provided
        if identity_document and upload_folder and identity_document.filename:
            identity_filename = secure_filename(identity_document.filename)
            if not Member._allowed_file(identity_filename):
                raise ValueError("Invalid identity document file type. Allowed types are: PNG, JPG, JPEG, PDF.")
            identity_path = os.path.join(upload_folder, identity_filename)
            identity_document.save(identity_path)
            member_data['identity_document_path'] = identity_path  # Save the identity document path

        # Handle photo ID upload if provided
        if photo_id and upload_folder and photo_id.filename:
            photo_filename = secure_filename(photo_id.filename)
            if not Member._allowed_file(photo_filename):
                raise ValueError("Invalid photo ID file type. Allowed types are: PNG, JPG, JPEG, PDF.")
            photo_path = os.path.join(upload_folder, photo_filename)
            photo_id.save(photo_path)
            member_data['photo_id_path'] = photo_path  # Save the photo ID path

        # Add the new member
        members.append(member_data)
        room_number = member_data.get('room_number')
        if room_number:
            # Find the room and update 'Occupied Beds'
            for room in rooms:
                if str(room['Room Number']) == str(room_number):
                    if room['Occupied Beds'] >= room['Capacity']:
                        raise ValueError(f"Room {room_number} is fully occupied!")
                    room['Occupied Beds'] += 1  # Increment 'Occupied Beds'
                    break
            else:
                raise ValueError(f"Room {room_number} not found!")
        write_data(members, rooms)


    @staticmethod
    def update_member(member_id, updated_data,file=None,upload_folder=None):
        members, rooms = read_data()
        for member in members:
            if member.get('member_id') == member_id:
                member.update(updated_data)
                if file and upload_folder and file.filename:
                    filename = secure_filename(file.filename)  # Secure the filename
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)  # Save the file
                    member['identity_document_path'] = file_path  # Update file path in member data
        write_data(members, rooms)

    @staticmethod
    def update_exit_date(member_id, exit_date):
        members, rooms = read_data()
        try:
            for member in members:
                if member.get('member_id') == member_id:
                    member['exit_date'] = exit_date
                    break
            else:
                raise ValueError("Member not found.")
            write_data(members, rooms)
        except Exception as e:
            raise Exception(f"Failed to update exit date: {str(e)}")

    @staticmethod
    def search_member(search_type, search_value):
        members, _ = read_data()
        search_results = []
        for member in members:
            if search_type == 'name' and search_value.lower() in member['Name'].lower():
                search_results.append(member)
            elif search_type == 'room' and search_value == member['Room Number']:
                search_results.append(member)
            elif search_type == 'phone' and search_value == member['Phone Number']:
                search_results.append(member)
        return search_results

    @staticmethod
    def get_member_by_id(member_id):
        members, _ = read_data()
        # Query member by ID from the database
        member = next((m for m in members if m['member_id'] == member_id), None)
        if not member:
            raise ValueError("Member not found")
        return member
