from flask import Flask, request, render_template, redirect, url_for, flash
import pandas as pd
from twilio.rest import Client
import schedule
import time
from threading import Thread
import os
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flashing messages

# Path to the Excel file
EXCEL_FILE = 'hostel_data.xlsx'

# Twilio configuration
TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

UPLOAD_FOLDER = 'uploads/'  # Directory to store member photos and identity proofs
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to read members and rooms from Excel file
def read_data():
    try:
        # Read the members sheet
        df_members = pd.read_excel(EXCEL_FILE, sheet_name='members')
        # Drop rows where critical fields (Room Number, Name) are missing
        df_members = df_members.dropna(subset=['Room Number', 'Name','member ID'])

        # Convert Room Number to string and strip spaces
        #df_members['Room Number'] = df_members['Room Number'].astype(str).str.strip()

        # Convert member ID, Phone Number to strings (to handle float-types like 544.0)
        df_members['member ID'] = df_members['member ID'].apply(lambda x: str(int(x)) if pd.notna(x) else '')
        df_members['Phone Number'] = df_members['Phone Number'].apply(lambda x: str(int(x)) if pd.notna(x) else '')
        df_members['Room Number'] = df_members['Room Number'].apply(lambda x: str(int(x)) if pd.notna(x) else '')

        # Replace NaN in text fields (like 'Last Fee Paid Date') with empty string
        df_members = df_members.fillna({'Last Fee Paid Date': ''})

        # Final dictionary of members
        members = df_members.to_dict(orient='records')

    except Exception as e:
        print(f"Error reading members sheet: {e}")
        members = []

    try:
        # Read the Rooms sheet
        df_rooms = pd.read_excel(EXCEL_FILE, sheet_name='Rooms')
        # Drop rows where Room Number is missing
        df_rooms = df_rooms.dropna(subset=['Room Number'])

        # Convert Room Number to string and strip spaces
        df_rooms['Room Number'] = df_rooms['Room Number'].astype(str).str.strip()

        # Final dictionary of rooms
        rooms = df_rooms.to_dict(orient='records')

    except Exception as e:
        print(f"Error reading Rooms sheet: {e}")
        rooms = []

    # Ensure at least an empty file structure exists
    create_excel_if_not_exists(members, rooms)
    return members, rooms



def create_excel_if_not_exists(members, rooms):
    try:
        if not os.path.exists(EXCEL_FILE):
            with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
                if not members:  # Empty members structure
                    members = [{'Name': '', 'Age': '', 'Room Number': '', 'member ID': '',
                                 'Phone Number': '', 'Fee Paid': 'No'}]
                if not rooms:  # Empty rooms structure
                    rooms = [{'Room Number': '', 'Capacity': ''}]
                pd.DataFrame(members).to_excel(writer, sheet_name='members', index=False)
                pd.DataFrame(rooms).to_excel(writer, sheet_name='Rooms', index=False)
    except Exception as e:
        print(f"Error creating Excel file: {e}")



# Function to write members and rooms to Excel file
def write_data(members, rooms):
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            pd.DataFrame(members).to_excel(writer, sheet_name='members', index=False)
            pd.DataFrame(rooms).to_excel(writer, sheet_name='Rooms', index=False)
        print("Data written successfully to Excel.")
    except Exception as e:
        print(f"Error writing to Excel: {e}")

# Function to send SMS
def send_sms(to_phone_number, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        print(f'SMS sent to {to_phone_number}')
    except Exception as e:
        print(f'Failed to send SMS to {to_phone_number}: {e}')

# Function to send fee reminders
def send_fee_reminders():
    members, _ = read_data()
    for member in members:
        if member['Fee Paid'] != 'Yes':
            send_sms(member['Phone Number'],
                     f"Dear {member['Name']}, your hostel fee is pending. Please pay it immediately.")

# Schedule fee reminders to be sent every day
schedule.every().day.at("08:00").do(send_fee_reminders)

# Function to run the scheduler
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.start()

@app.route('/')
def index():
    members, rooms = read_data()
    num_members = len(members)
    num_rooms = len(rooms)
    num_occupied_rooms = len(set(member['Room Number'] for member in members))
    num_free_rooms = num_rooms - num_occupied_rooms

    return render_template('index.html', num_members=num_members, num_rooms=num_rooms, num_free_rooms=num_free_rooms, num_occupied_rooms=num_occupied_rooms)

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    members, rooms = read_data()  # Read members and rooms data

    # Example room data
    # rooms format: [{'Room Number': '101', 'Beds': [{'Bed Number': '1', 'Bed Type': 'Single', 'Occupied': False}]}]

    if request.method == 'POST':
        # Basic member details
        name = request.form['name']
        phone_number = request.form['phone_number']
        dob = request.form['dob']
        age = request.form['age']
        permanent_address = request.form['permanent_address']
        purpose_of_staying = request.form['purpose_of_staying']
        date_of_joining = request.form['date_of_joining']
        father_name = request.form['father_name']
        family_number = request.form['family_number']
        office_address = request.form['office_address']
        aadhar_number = request.form['aadhar_number']
        date_of_exit = '31-12-9999'  # Default high-end exit date

        # Room and bed details
        room_number = request.form['room_number']
        bed_type = request.form['bed_type']
        bed_number = request.form['bed_number']

        # Fee details
        monthly_fee = request.form['monthly_fee']
        advance_amount = request.form['advance_amount']

        # Process uploaded files
        photo = request.files['photo']
        id_proof = request.files['id_proof']

        # Calculate age again on the backend to validate
        dob_date = datetime.datetime.strptime(dob, '%Y-%m-%d').date()
        today = datetime.date.today()
        calculated_age = today.year - dob_date.year
        if (today.month, today.day) < (dob_date.month, dob_date.day):  # Adjust for month/day
            calculated_age -= 1

        # Check if the age provided matches the calculated age
        if age != calculated_age:
            return "Invalid Age Calculated!", 400

        photo_path = ''
        id_proof_path = ''

        # Save photo if provided
        if photo and allowed_file(photo.filename):
            photo_filename = secure_filename(photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            photo.save(photo_path)

        # Save identity proof if provided
        if id_proof and allowed_file(id_proof.filename):
            id_proof_filename = secure_filename(id_proof.filename)
            id_proof_path = os.path.join(UPLOAD_FOLDER, id_proof_filename)
            id_proof.save(id_proof_path)

        # Validate room and bed availability
        selected_room = next((room for room in rooms if room['Room Number'] == room_number), None)
        if not selected_room:
            return "Invalid room selected!", 400

        selected_bed = next((bed for bed in selected_room['Beds']
                             if
                             bed['Bed Number'] == bed_number and bed['Bed Type'] == bed_type and not bed['Occupied']),
                            None)

        if not selected_bed:
            return "Bed not available or assigned to another member!", 400

        # Mark the selected bed as occupied
        selected_bed['Occupied'] = True

        # Create a new member record
        new_member = {
            'Name': name,
            'Phone Number': phone_number,
            'Date of Birth': dob,
            'Age': age,
            'Permanent Address': permanent_address,
            'Purpose of Staying': purpose_of_staying,
            'Date of Joining': date_of_joining,
            'Father Name': father_name,
            'Family Number/Reference Number': family_number,
            'Office Address': office_address,
            'Aadhar Number': aadhar_number,
            'Date of Exit': date_of_exit,
            'Room Number': room_number,
            'Bed Type': bed_type,
            'Bed Number': bed_number,
            'Monthly Fee': monthly_fee,
            'Advance Amount': advance_amount,
            'Photo Path': photo_path,
            'Identity Proof Path': id_proof_path
        }

        # Add the new member to the members list and update the data in the Excel file
        members.append(new_member)
        write_data(members, rooms)

        return redirect(url_for('search_member'))

    return render_template('add_member.html', rooms=rooms)


@app.route("/get_available_beds/<room_number>", methods=["GET"])
def get_available_beds(room_number):
    members, rooms = read_data()  # Load existing member and room data
    room_number=str(room_number).strip()

    # Find the room matching the provided room number
    selected_room = next((room for room in rooms if str(room["Room Number"]).strip() == room_number), None)
    print(f"Selected Room: {selected_room}")

    if not selected_room:
        return {"error": "Invalid room number"}, 404

    # Determine Bed Type dynamically using the Room Capacity
    room_capacity = selected_room.get("Capacity")  # Get capacity (e.g., 4, 5)
    print(f"Room Capacity: {room_capacity}")

    if not room_capacity:
        return {"error": "Room capacity not defined"}, 400

    bed_type = f"{room_capacity}-sharing"  # Generate Bed Type dynamically (e.g., '4-sharing')

    bed_capacity=room_capacity
    # Dynamically generate bed data
    beds = [{"Bed Number": str(i), "Occupied": False} for i in range(1, bed_capacity + 1)]

    # Get all unoccupied beds
    available_beds = [bed for bed in beds if not bed["Occupied"]]
    print(f"Available Beds: {available_beds}")


    # Format the response to include bed type and available bed numbers
    return {
        "bed_type": bed_type,
        "beds": [{"Bed Number": bed["Bed Number"]} for bed in available_beds]
    }, 200



@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    members, rooms = read_data()

    if request.method == 'POST':
        room_number = request.form['room_number']
        capacity = request.form['capacity']

        # Check for duplicate room number
        if any(str(room['Room Number']) == str(room_number) for room in rooms):
            flash('Room number already exists. Please use a unique room number.')
            return redirect(url_for('add_room'))

        # Add new room
        room = {
            'Room Number': str(room_number),  # Ensure Room Number is string
            'Capacity': capacity
        }
        rooms.append(room)

        # Sort rooms based on numeric Room Number
        rooms = sorted(rooms, key=lambda x: int(x['Room Number']) if str(x['Room Number']).isdigit() else str(
            x['Room Number']))

        # Save sorted rooms
        write_data(members, rooms)

        flash(f"Room {room_number} added successfully!")
        return redirect(url_for('add_room'))

    # Sort rooms before displaying
    rooms = sorted(rooms,
                   key=lambda x: int(x['Room Number']) if str(x['Room Number']).isdigit() else str(x['Room Number']))

    # Pass sorted rooms to the template for management
    return render_template('add_room.html', rooms=rooms)


@app.route('/edit_room/<room_number>', methods=['GET', 'POST'])
def edit_room(room_number):
    members, rooms = read_data()
    room_number=str(room_number).strip()

    room = next((room for room in rooms if str(room['Room Number']).strip() == room_number), None)

    if not room:
        flash(f"Room {room_number} not found!")
        return redirect(url_for('add_room'))

    if request.method == 'POST':
        new_capacity = request.form['capacity']
        room['Capacity'] = new_capacity
        write_data(members, rooms)
        flash(f"Room {room_number} updated successfully.")
        return redirect(url_for('add_room'))

    return render_template('edit_room.html', room=room)

@app.route('/search_member', methods=['GET', 'POST'])
def search_member():
    members, rooms = read_data()  # Read data from the Excel file
    search_result = {}

    if request.method == 'POST':
        # Get search criteria
        search_type = request.form.get('search_type')  # Dropdown selection: "name", "room", "phone"
        search_value = request.form.get('search_value', '').strip()  # The actual search value

        # Filter logic based on search type
        for member in members:
            if search_type == 'name' and search_value.lower() in member['Name'].lower():
                member_room = str(member['Room Number']).strip()
                if member_room not in search_result:
                    search_result[member_room] = []
                search_result[member_room].append(member)
            elif search_type == 'room' and search_value == str(member['Room Number']).strip():
                member_room = str(member['Room Number']).strip()
                if member_room not in search_result:
                    search_result[member_room] = []
                search_result[member_room].append(member)
            elif search_type == 'phone' and search_value == str(member['Phone Number']).strip():
                member_room = str(member['Room Number']).strip()
                if member_room not in search_result:
                    search_result[member_room] = []
                search_result[member_room].append(member)

    # Debugging: Print what the search result contains
    print("Search Results Grouped by Room:", search_result)

    return render_template('search_member.html', search_result=search_result, rooms=rooms)


@app.route('/remove_member', methods=['POST'])
def remove_member():
    # This will now be called from the "Remove" button in `search_member` results
    member_id = request.form.get('member_id', '').strip()
    members, rooms = read_data()  # Get all the data

    # Remove the member with the matching member ID
    members = [member for member in members if str(member['member ID']) != member_id]

    # Save the updated data back to the file
    write_data(members, rooms)
    return redirect(url_for('search_member'))


@app.route('/edit_member/<member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    members, rooms = read_data()  # Get the existing data
    member_to_edit = next((member for member in members if str(member['member ID']) == member_id), None)

    if not member_to_edit:
        return "member not found!", 404  # Return error if member doesn't exist

    if request.method == 'POST':
        # Update the member's information with the provided form data
        member_to_edit['Name'] = request.form['name']
        member_to_edit['Age'] = request.form['age']
        member_to_edit['Room Number'] = request.form['room_number']
        member_to_edit['Phone Number'] = request.form['phone_number']
        member_to_edit['Fee Paid'] = request.form['fee_status']

        # Save the updates back to the file
        write_data(members, rooms)
        return redirect(url_for('search_member'))

    # Render the edit form pre-filled with the member's data
    return render_template('edit_member.html', member=member_to_edit)


@app.route('/search_room', methods=['GET', 'POST'])
def search_room():
    members, rooms = read_data()
    return render_template('search_room.html', rooms=rooms)

@app.route('/delete_room/<room_number>', methods=['POST'])
def delete_room(room_number):
    members, rooms = read_data()
    room_number=str(room_number).strip()

    # Check if the room has any members assigned
    if any(str(member['Room Number']).strip() == room_number for member in members):
        flash('Cannot delete room. It has members assigned.')
        return redirect(url_for('search_room'))

    # Delete the room
    rooms = [room for room in rooms if str(room['Room Number']).strip() != room_number]
    write_data(members, rooms)

    flash(f'Room {room_number} deleted successfully.')
    return redirect(url_for('search_room'))

@app.route('/view_member/<member_id>', methods=['GET'])
def view_member(member_id):
    members, _ = read_data()
    member = next((s for s in members if str(s['Aadhar Number']) == str(member_id)), None)

    if not member:
        return "member not found!", 404

    # Render a page showing the member's details, including links to their photo and ID proof
    return render_template('view_member.html', member=member)


@app.route('/fees', methods=['GET'])
def fees():
    members, _ = read_data()

    # Separate into paid and pending fee groups
    paid_fees = [member for member in members if member['Fee Paid'] == 'Yes']
    pending_fees = [member for member in members if member['Fee Paid'] != 'Yes']

    return render_template('add_fee_details.html.html', paid_fees=paid_fees, pending_fees=pending_fees)


@app.route('/pay_fee/<member_id>', methods=['POST'])
def pay_fee(member_id):
    members, rooms = read_data()

    # Find the member
    member = next((s for s in members if s['member ID'] == member_id), None)
    if not member:
        flash(f"member with ID {member_id} not found.")
        return redirect(url_for('fees'))

    # Mark fee as paid
    member['Fee Paid'] = 'Yes'
    write_data(members, rooms)
    flash(f"Fee marked as paid for member ID {member_id}.")
    return redirect(url_for('fees'))

def calculate_monthly_fees(joining_date, bed_type):
    # Assume rates (3-sharing: $300/month, 4-sharing: $250/month)
    rates = {
        '3': 9000,
        '4': 7500,
        '5': 7000,
        '6': 6000
    }
    start_date = pd.to_datetime(joining_date)
    current_date = pd.Timestamp.now()

    # Calculate months since joining (full months only)
    months_since_joining = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)

    # Fee based on months since joining
    total_fee_due = months_since_joining * rates[bed_type]
    return total_fee_due

@app.route('/fee_dashboard', methods=['GET'])
def fee_dashboard():
    members, _ = read_data()

    fee_summary = {
        'paid_on_time': len([s for s in members if s['Fee Paid'] == 'Yes']),
        'not_paid': len([s for s in members if s['Fee Paid'] != 'Yes'])
    }

    return render_template('fee_dashboard.html', fee_summary=fee_summary)


def send_reminders_to_unpaid():
    members, _ = read_data()
    for member in members:
        if member['Fee Paid'] != 'Yes':
            send_sms(member['Phone Number'],
                     f"Dear {member['Name']}, your hostel fee is overdue. Please pay immediately.")

if __name__ == "__main__":
    app.run(debug=True)
