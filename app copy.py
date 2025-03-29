import os
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash

from fee import calculate_payment_date
from member import Member
from room import Room

# Define your upload folder (where files will be saved)
UPLOAD_FOLDER = 'uploads/'  # Path to save uploaded files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}  # Allowed file extensions

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.secret_key = 'supersecretkey'

# Index Route
@app.route('/')
def index():
    members = Member.get_all_members()
    rooms = Room.get_all_rooms()
    Bed_info=Room.get_bed_count()
    total_no_beds = Bed_info[0]
    Num_free_beds = Bed_info[2]
    Num_Occ_beds = Bed_info[1]

    return render_template('index.html',
                           members=len(members), rooms=len(rooms)
                           ,Num_free_beds=Num_free_beds,Num_Occ_beds=Num_Occ_beds
                           ,total_no_beds=total_no_beds)


# Add Member Route
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        # Handle form data
        member_data = request.form.to_dict()

        # Handle file uploads
        file = request.files.get('identity_document')  # Get file from the form
        photo_id = request.files.get('photo_id')

        try:
            # Call the function to add the member
            Member.add_member(
                member_data=member_data,
                identity_document=file,
                photo_id=photo_id,
                upload_folder=app.config['UPLOAD_FOLDER']
            )

            # On success, redirect to the index page with a success message
            flash("Member added successfully!", "success")
            return redirect(url_for('index'))

        except ValueError as e:
            # Handle validation errors from the add_member function
            flash(f"Error: {str(e)}", "danger")
            return redirect(request.url)

        except Exception as e:
            # Handle unexpected exceptions
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return redirect(request.url)

    # Render the form for GET requests
    return render_template('add_member.html')




@app.route('/search_member', methods=['GET', 'POST'])
def search_member():
    search_results = []  # Initialize an empty results list

    if request.method == 'POST':  # If the form is submitted
        search_query = request.form.get('search_query')  # Retrieve the query from the form
        search_type = request.form.get('search_type')  # Retrieve the selected search type (name, room, etc.)

        # Fetch all members
        members = Member.get_all_members()

        # Filter members based on the selected criteria (name, room, or phone)
        if search_type == 'name':
            search_results = [member for member in members if str(search_query.lower()).strip() in str(member.get('name', '').lower()).strip()]
        elif search_type == 'room':
            search_results = [member for member in members if str(member.get('room_number')).strip() == str(search_query).strip()]
        elif search_type == 'phone':
            search_results = [member for member in members if search_query in member.get('phone_number', '')]

    # Render the search results (if any) or provide an empty search result set
    return render_template('search_member.html', search_results=search_results)


@app.route('/edit_member/<member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    # Get the member details using member ID
    member = Member.get_member_by_id(member_id)

    if request.method == 'POST':
        # Fetch selected columns from the form
        selected_columns = request.form.getlist('columns')

        # Create a dictionary of updates with only selected columns
        updated_data = {
            column: request.form.get(column) for column in selected_columns if column in member
        }

        try:
            # Update the selected fields for the member
            Member.update_member(member_id, updated_data)
            flash("Member updated successfully!", "success")
            return redirect(url_for('search_member'))
        except Exception as e:
            flash(f"Error updating member: {str(e)}", "danger")
            return redirect(request.url)

    # Render the edit member form (GET request)
    return render_template('edit_member.html', member=member)





@app.route('/delete_member/<member_id>', methods=['GET', 'POST'])
def delete_member(member_id):
    member = Member.get_member_by_id(member_id)
    room_number = member.get('room_number')
    if request.method == 'POST':  # Handle the form submission for editing
        delete_data = request.form.to_dict()  # Get the updated form fields
        try:
            Member.update_member(member_id, delete_data)
            if room_number:
                room = Room.get_room_by_number(room_number)
                if room:
                    # Update the room's bed counts: Occupied -= 1, Free += 1
                    updated_occupied = max(0, room['Occupied Beds'] - 1)

                    # Save the updated room data
                    Room.modify_room(room_number, updated_occupied)

            flash("Member marked as expired and room data updated successfully.", "success")
        except Exception as e:
            flash(f"Error marking member as expired and updating room {str(e)}", "danger")
    return render_template('delete_member.html', member=member)





# Add Room Route
@app.route('/manage_rooms', methods=['GET', 'POST'])
def manage_rooms():
    if request.method == 'POST':
        # Add new room
        room_data = {
            'Room Number': request.form['room_number'],
            'Capacity': int(request.form['capacity']),
            'Floor': int(request.form['floor']),
            'Occupied Beds': 0,  # New room starts with no occupied beds
        }
        Room.add_room(room_data)
        flash(f"Room {room_data['Room Number']} added successfully!")

    # Fetch all rooms and floor-wise summary for display
    rooms = Room.get_all_rooms()
    rooms = sorted(rooms, key=lambda room: room['Room Number'])
    for room in rooms:
        if 'Occupied Beds' not in room:
            room['Occupied Beds'] = 0
    floor_data = Room.get_floor_wise_summary()
    return render_template('add_and_view_rooms.html', rooms=rooms, floor_data=floor_data)

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    # Logic to handle the addition of a room
    if request.method == 'POST':
        room_data = {
            'Room Number': request.form['room_number'],
            'Capacity': int(request.form['capacity']),
            'Floor': int(request.form['floor'])
        }
        Room.add_room(room_data)  # Save room details (modify this function as per the data handling logic)
        flash(f"Room {room_data['Room Number']} added successfully!")
        return redirect(url_for('manage_rooms'))  # Redirect to the appropriate route after a successful room addition
    return render_template('add_room.html')  # For GET requests, show the 'Add Room' form


# Edit Room Route
@app.route('/edit_room/<room_number>', methods=['GET', 'POST'])
def edit_room(room_number):
    if request.method == 'POST':
        new_capacity = request.form['capacity']
        new_floor = request.form['floor']
        Room.update_room(int(room_number), int(new_capacity),int(new_floor))
        flash(f"Room {room_number} updated successfully!")
        return redirect(url_for('manage_rooms'))  # Redirect to manage_rooms view

    # Get the room details to pre-fill the form
    try:
        room = next(room for room in Room.get_all_rooms() if str(room['Room Number']) == str(room_number))
    except StopIteration:
        flash(f"Room {room_number} not found.")
        return redirect(url_for('manage_rooms'))  # Redirect if room doesn't exist
    return render_template('edit_room.html', room=room)


# Delete Room Route
@app.route('/delete_room/<room_number>', methods=['POST'])
def delete_room(room_number):
    if Room.has_assigned_members(room_number):
        flash("Cannot delete room. Members are assigned to it.")
    else:
        Room.delete_room(room_number)
        flash(f"Room {room_number} deleted successfully!")
    return redirect(url_for('manage_rooms'))  # Redirect to manage_rooms view


@app.route('/fee-dashboard')
def fee_dashboard():
    return render_template('fee_dashboard.html')

# Folder to save the generated fee sheets
GENERATED_SHEETS_FOLDER = 'generated_sheets/'
os.makedirs(GENERATED_SHEETS_FOLDER, exist_ok=True)  # Ensure folder exists


@app.route('/generate_fee_sheet', methods=['POST'])
def generate_fee_sheet():
    """
    Generate and save an Excel workbook with the fee details for the current month.
    """

    # Step 1: Fetch active members
    active_members = Member.get_all_members()  # Assuming this returns a list of member dictionaries

    # Step 2: Prepare data for the Excel sheet
    sheet_name = f"fee_detail_{datetime.now().strftime('%B')}"  # Example: fee_detail_October

    # Columns for the sheet
    headers = [
        "member_id", "name", "room_number", "fee_amount",
        "payment_date", "Amount_Paid_date", "paid_amount",
        "fee_paid_status", "advance_amount", "advance_status", "balance_amount"
    ]

    # Populate rows with member data
    excel_data = []
    for member in active_members:
        joining_date = member.get('joining_date')
        payment_date = calculate_payment_date(joining_date) if joining_date else ""
        row = {
            "member_id": member.get('member_id'),
            "name": member.get('name'),
            "room_number": member.get('room_number'),
            "fee_amount": member.get('fee_amount'),
            "payment_date": payment_date,
            "Amount_Paid_date": "",
            "paid_amount": "",
            "fee_paid_status": "",
            "advance_amount": "",
            "advance_status": "",
            "balance_amount": ""
        }
        excel_data.append(row)

    # Step 3: Create a DataFrame
    df = pd.DataFrame(excel_data, columns=headers)

    # Step 4: Save the DataFrame to an Excel file
    file_path = os.path.join(GENERATED_SHEETS_FOLDER, f"{sheet_name}.xlsx")
    df.to_excel(file_path, index=False, sheet_name=sheet_name)

    # Optional: Notify that the file was created
    print(f"Fee sheet saved to: {file_path}")

    # Render or return a success message
    return f"Fee sheet generated and saved as {file_path}"


@app.route('/fee_details', methods=['GET', 'POST'])
def fee_details():
    # Path to the fee sheet for the current month
    current_month = datetime.now().strftime('%B')  # Example: October
    fee_sheet_filename = os.path.join(GENERATED_SHEETS_FOLDER, f"fee_detail_{current_month}.xlsx")

    if not os.path.exists(fee_sheet_filename):
        # If the fee sheet doesn't exist, notify the user
        flash("Fee sheet for the current month has not been generated yet.", "danger")
        return redirect(url_for('fee_dashboard'))

    # Initialize search results
    search_results = []

    if request.method == 'POST':  # If the user submits the search form
        search_query = request.form.get('search_query')
        search_type = request.form.get('search_type')

        # Load the fee sheet into a DataFrame
        fee_data = pd.read_excel(fee_sheet_filename)

        # Perform search based on the selected criteria
        if search_type == 'name':
            search_results = fee_data[fee_data['name'].str.contains(search_query, case=False, na=False)].to_dict(
                'records')
        elif search_type == 'room':
            search_results = fee_data[fee_data['room_number'] == int(search_query)].to_dict('records')
        elif search_type == 'phone':
            # Assuming phone field exists in the fee sheet
            search_results = fee_data[fee_data['phone'] == search_query].to_dict('records')

    # Render the fee details page with search results
    return render_template('fee_details.html', search_results=search_results)


@app.route('/edit_fee/<member_id>', methods=['GET', 'POST'])
def edit_fee(member_id):
    # Load the fee sheet for the current month
    current_month = datetime.now().strftime('%B')
    fee_sheet_filename = os.path.join(GENERATED_SHEETS_FOLDER, f"fee_detail_{current_month}.xlsx")

    # Ensure the file exists
    if not os.path.exists(fee_sheet_filename):
        flash("Fee sheet for the current month has not been generated yet.", "danger")
        return redirect(url_for('fee_details'))

    # Load the fee sheet into a DataFrame
    fee_data = pd.read_excel(fee_sheet_filename)

    # Find the specific member's record
    member_fee = fee_data[fee_data['member_id'] == str(member_id)].iloc[0]
    print(member_fee)

    if request.method == 'POST':
        # Fetch selected columns from the form
        selected_columns = request.form.getlist('columns')
        for column in selected_columns:
            if column in member_fee:
                fee_data.loc[fee_data['member_id'] == str(member_id), column] = request.form.get(column,
                                                                                                 member_fee[column])
        # Save back to the file
        fee_data.to_excel(fee_sheet_filename, index=False)
        flash("Fee details updated successfully!", "success")
        return redirect(url_for('fee_details'))

    return render_template('edit_fee.html', member_fee=member_fee)

if __name__ == '__main__':
    app.run(debug=True)
