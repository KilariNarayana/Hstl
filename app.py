import os
from datetime import datetime, date

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash,session
from werkzeug.utils import secure_filename

from fee import calculate_payment_date
from member import Member
from room import Room
from fee_detail import FeeDetail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Define your upload folder (where files will be saved)
UPLOAD_FOLDER = 'uploads/'  # Path to save uploaded files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}  # Allowed file extensions

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.secret_key = 'supersecretkey'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, member_name, file_type):
    if file and allowed_file(file.filename):
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{member_name}_{file_type}.{extension}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return file_path
    return None

# Index Route
@app.route('/')
def index():
    members = Member.get_all_members()
    rooms = Room.get_all_rooms()
    Room.recalculate_all_occupied_beds()  # Recalculate occupied beds based on active members
    Bed_info = Room.get_bed_count()
    total_no_beds = Bed_info[0]
    Num_free_beds = Bed_info[2]
    Num_Occ_beds = Bed_info[1]

    return render_template('index.html',
                           members=len(members), rooms=len(rooms),
                           Num_free_beds=Num_free_beds, Num_Occ_beds=Num_Occ_beds,
                           total_no_beds=total_no_beds)

# Add Member Route
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        # Handle form data
        member_data = request.form.to_dict()
        member_name = member_data.get('name', 'unknown').replace(' ', '_')

        # Handle file uploads
        identity_document = request.files.get('identity_document')
        photo_id = request.files.get('photo_id')

        identity_document_path = save_file(identity_document, member_name, 'ID_Document')
        photo_id_path = save_file(photo_id, member_name, 'ID_Photo')

        # Add file paths to member data
        member_data['identity_document_path'] = identity_document_path
        member_data['photo_id_path'] = photo_id_path

        try:
            # Update room capacity
            room_number = int(member_data['room_number'])
            room = Room.get_room_by_number(room_number)
            if not room:
                raise ValueError(f"Room {room_number} not found.")
            
            # Call the function to add the member
            Member.add_member(member_data)
            Room.update_occupied_beds(room_number)

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
    selected_columns = []  # Initialize an empty list for selected columns

    if request.method == 'POST':  # If the form is submitted
        search_query = request.form.get('search_query')  # Retrieve the query from the form
        search_type = request.form.get('search_type')  # Retrieve the selected search type (name, room, etc.)
        selected_columns = request.form.getlist('columns')  # Retrieve the selected columns

        # Fetch all members
        members = Member.get_all_members()
    
        # Filter members based on the selected criteria (name, room, or phone)
        if search_type == 'name':
            search_results = [member for member in members if str(search_query.lower()).strip() in str(member.get('name', '').lower()).strip()]
        elif search_type == 'room':
            search_results = [member for member in members if str(member.get('room_number')).strip() == str(search_query).strip()]
        elif search_type == 'phone':
            search_results = [member for member in members if search_query in member.get('phone_number', '')]

        # If 'all' is selected, include all columns except 'member_id' and 'exit_date'
        if 'all' in selected_columns:
            selected_columns = [key for key in members[0].keys() if key not in ['member_id', 'exit_date']]

    # Render the search results (if any) or provide an empty search result set
    return render_template('search_member.html', search_results=search_results, selected_columns=selected_columns)

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

@app.route('/delete_member/<member_id>', methods=['POST'])
def delete_member(member_id):
    try:
        member = Member.get_member_by_id(member_id)
        room_number = member.get('room_number')

        # Mark the member as expired by updating the exit_date
        Member.update_exit_date(member_id, date.today().isoformat())

        if room_number:
            Room.update_occupied_beds(room_number)

        flash("Member marked as expired and room data updated successfully.", "success")
    except Exception as e:
        flash(f"Error marking member as expired and updating room: {str(e)}", "danger")

    return redirect(url_for('search_member'))

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
        flash(f"Room {room_data['room_number']} added successfully!")

    # Recalculate occupied beds based on active members
    Room.recalculate_all_occupied_beds()

    # Fetch all rooms and floor-wise summary for display
    rooms = Room.get_all_rooms()
    rooms = sorted(rooms, key=lambda room: room['room_number'])
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
            'room_number': request.form['room_number'],
            'capacity': int(request.form['capacity']),
            'floor': int(request.form['floor'])
        }
        Room.add_room(room_data)  # Save room details (modify this function as per the data handling logic)
        flash(f"Room {room_data['room_number']} added successfully!")
        return redirect(url_for('manage_rooms'))  # Redirect to the appropriate route after a successful room addition
    return render_template('add_room.html')  # For GET requests, show the 'Add Room' form

# Edit Room Route
@app.route('/edit_room/<int:room_number>', methods=['GET', 'POST'])
def edit_room(room_number):
    room = Room.get_room_by_number(room_number)
    if not room:
        flash(f"Room {room_number} not found.", "Unable to edit room as Room Number not present.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        capacity = request.form.get('capacity')
        floor = request.form.get('floor')

        try:
            Room.update_room(room_number, int(capacity), int(floor))
            flash("Room details updated successfully!", "success")
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f"Error: {str(e)}", "danger")
            return redirect(request.url)

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


@app.route('/generate_fee_details', methods=['POST'])
def generate_fee_details():
    """
    Generate and save fee details for the current month in the database.
    """
    # Step 1: Fetch active members
    active_members = Member.get_all_members()  # Assuming this returns a list of member dictionaries

    # Step 2: Prepare data for the fee details
    fee_details = []
    current_year_month = datetime.now().strftime('%Y%m')
    sequence_number = 1

    for member in active_members:
        # Fetch the previous month's fee details for the member
        previous_fee_detail = FeeDetail.get_latest_fee_detail_by_member_id(member.get('member_id'))

        # Calculate the previous month's balance
        previous_month_balance = 0
        if previous_fee_detail:
            balance_amount = previous_fee_detail['fee_amount'] - previous_fee_detail['payment_paid_amount']
            if balance_amount > 0:
                previous_month_balance = balance_amount

        # Calculate the total payment amount for the current month
        current_month_payment_amount = member.get('fee_amount') + previous_month_balance

        # Generate a unique fee ID for the current month
        fee_sequence_number = f"{current_year_month}{sequence_number:04d}"

        # Prepare the fee detail for the current month
        fee_detail = {
            "member_id": member.get('member_id'),
            "name": member.get('name'),
            "room_number": member.get('room_number'),
            "fee_amount": member.get('fee_amount'),
            "previous_month_balance": previous_month_balance,
            "payment_paid_amount": 0,  # Initialize to 0 for the new month
            "advance_paid_amount": 0,
            "fee_id": fee_sequence_number,
            "amount_paid_date": None,
            "due_date": calculate_payment_date(member.get('joining_date')) if member.get('joining_date') else None
        }

        # Reset the previous_month_balance to 0 if the balance is fully paid
        if previous_month_balance > 0 and balance_amount == 0:
            fee_detail["previous_month_balance"] = 0

        fee_details.append(fee_detail)
        sequence_number += 1

    # Step 3: Save fee details to the database
    for detail in fee_details:
        FeeDetail.add_fee_detail(detail)

    # Render or return a success message
    flash("Fee details generated successfully for the current month!", "success")
    return redirect(url_for('fee_dashboard'))


@app.route('/fee_dashboard', methods=['GET', 'POST'])
def fee_dashboard():
    # Clear session if the user refreshes the page or navigates to the dashboard without filtering
    if request.method == 'GET' and not request.args.get('sort_by'):
        session.pop('filtered_fee_details', None)

    filter_type = None
    filter_due_date = None
    filter_name = None
    filter_room_number = None
    filter_amount_paid_status = None
    filter_advance_paid_status = None
    sort_by = request.args.get('sort_by', 'room_number')  # Default sort by room_number
    sort_order = request.args.get('sort_order', 'asc')  # Default sort order is ascending

    fee_details = []  # Initialize as empty to hide the table until a search is performed

    if request.method == 'POST':
        # Handle filters
        filter_type = request.form.get('filter_type')
        if filter_type == 'due_date':
            filter_due_date = request.form.get('due_date')
        elif filter_type == 'room_number':
            filter_room_number = request.form.get('room_number')
        elif filter_type == 'name':
            filter_name = request.form.get('name')

        filter_amount_paid_status = request.form.get('amount_paid_status')
        filter_advance_paid_status = request.form.get('advance_paid_status')

        # Fetch filtered fee details from the database
        fee_details = FeeDetail.get_all_fee_details(
            filter_due_date, filter_name, filter_room_number,
            filter_amount_paid_status, filter_advance_paid_status
        )

        # Store the filtered data in the session
        session['filtered_fee_details'] = fee_details

    elif 'filtered_fee_details' in session:
        # Retrieve filtered data from the session
        fee_details = session['filtered_fee_details']

    # Sort fee details by the selected column and order
    reverse = True if sort_order == 'desc' else False
    fee_details = sorted(
        fee_details,
        key=lambda x: (
            datetime.strptime(x.get(sort_by, ''), '%a, %d %b %Y %H:%M:%S %Z').toordinal() if sort_by == 'due_date' and x.get(sort_by) and ',' in x.get(sort_by) else
            datetime.strptime(x.get(sort_by, ''), '%Y-%m-%d').toordinal() if sort_by == 'due_date' and x.get(sort_by) else
            (x.get(sort_by, '') if isinstance(x.get(sort_by, ''), (float, int)) else str(x.get(sort_by, '')) or '')
        ),
        reverse=reverse
    )

    # Fetch all fee details for summary calculations (ignoring filters)
    all_fee_details = FeeDetail.get_all_fee_details()

    # Calculate summary details for all members
    total_amount_current_month = sum(fee['fee_amount'] for fee in all_fee_details)
    total_amount_received_so_far = sum(fee['payment_paid_amount'] for fee in all_fee_details)
    total_previous_month_balance = sum(fee['previous_month_balance'] for fee in all_fee_details)
    balance_amount = total_amount_current_month - total_amount_received_so_far
    no_of_members_paid = sum(1 for fee in all_fee_details if fee['fee_paid_status'] == 'Y')
    total_members = len(all_fee_details)
    balance_members = total_members - no_of_members_paid

    # Pass fee details and summary data to the template
    return render_template('fee_dashboard.html', fee_details=fee_details,
                           total_amount_current_month=total_amount_current_month,
                           total_amount_received_so_far=total_amount_received_so_far,
                           total_previous_month_balance=total_previous_month_balance,
                           balance_amount=balance_amount,
                           no_of_members_paid=no_of_members_paid,
                           balance_members=balance_members,
                           filter_type=filter_type,
                           filter_due_date=filter_due_date,
                           filter_name=filter_name,
                           filter_room_number=filter_room_number,
                           filter_amount_paid_status=filter_amount_paid_status,
                           filter_advance_paid_status=filter_advance_paid_status,
                           sort_by=sort_by,
                           sort_order=sort_order)

@app.route('/edit_fee/<fee_id>', methods=['GET', 'POST'])
def edit_fee(fee_id):
    # Fetch the fee details for the given fee_id
    fee_detail = FeeDetail.get_fee_detail_by_id(fee_id)

    if request.method == 'POST':
        # Get the new payment and advance amounts from the form
        new_payment_paid_amount = float(request.form.get('payment_paid_amount', 0))
        new_advance_paid_amount = float(request.form.get('advance_paid_amount', 0))
        amount_paid_date = request.form.get('amount_paid_date')

        # Calculate the updated payment and advance amounts
        updated_payment_paid_amount = fee_detail['payment_paid_amount'] + new_payment_paid_amount
        updated_advance_paid_amount = fee_detail['advance_paid_amount'] + new_advance_paid_amount

        # Ensure that the payment and advance amounts do not exceed the respective limits
        if updated_payment_paid_amount > fee_detail['fee_amount']:
            updated_payment_paid_amount = fee_detail['fee_amount']
        if updated_advance_paid_amount > 2000:  # Limit advance amount to 2000
            updated_advance_paid_amount = 2000

        # Stop updates if the payment and advance amounts have reached their respective limits
        if fee_detail['payment_paid_amount'] == fee_detail['fee_amount'] and \
           fee_detail['advance_paid_amount'] == 2000:
            flash("Payment and advance amounts are already fully paid for the current month.", "info")
            return redirect(url_for('fee_dashboard'))

        # Prepare the updated data
        updated_data = {
            "payment_paid_amount": updated_payment_paid_amount,
            "advance_paid_amount": updated_advance_paid_amount,
            "amount_paid_date": datetime.strptime(amount_paid_date, '%Y-%m-%d').date() if amount_paid_date else None
        }

        try:
            # Update the fee details in the database
            FeeDetail.update_fee_detail(fee_id, updated_data)
            flash("Fee details updated successfully!", "success")
            return redirect(url_for('fee_dashboard'))
        except Exception as e:
            flash(f"Error updating fee details: {str(e)}", "danger")
            return redirect(request.url)

    # Render the edit fee form for GET requests
    return render_template('edit_fee.html', fee_detail=fee_detail)

def format_unpaid_fees_message(unpaid_members):
    """
    Format the message for members with unpaid fees.
    """
    message = "The following members have not paid their fees before the due date:\n\n"
    message += "Member Name\tRoom Number\tDue Date\tFee Amount\n"
    message += "-" * 50 + "\n"

    for member in unpaid_members:
        message += f"{member['name']}\t{member['room_number']}\t{member['due_date'].strftime('%d-%b-%Y')}\t{member['fee_amount']}\n"

    return message



def send_email_notification(subject, message, recipient_email):
    """
    Send an email notification.
    """
    sender_email = "gkguesthouse97@gmail.com"
    sender_password = "ckfklujbzvyirykx"

    try:
        # Set up the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


last_notification_date = None  # Global variable to track the last notification date

@app.route('/send_notifications', methods=['GET'])
def send_notifications():
    global last_notification_date

    # Check if the notification has already been sent today
    today_date = datetime.now().date()
    if last_notification_date == today_date:
        flash("Notifications have already been sent today.", "info")
        return redirect(url_for('fee_dashboard'))

    # Fetch members with unpaid fees
    unpaid_members = FeeDetail.get_members_with_unpaid_fees()
    
    if not unpaid_members:
        flash("No unpaid members found.", "info")
        return redirect(url_for('fee_dashboard'))
    
    # Format the notification message
    message = format_unpaid_fees_message(unpaid_members)
    
    # Send email notification
    recipient_email = "gkguesthouse97@gmail.com"  # Replace with the user's email
    send_email_notification("Unpaid Fees Notification", message, recipient_email)
    
    # Send WhatsApp notification (optional)
    # recipient_number = "+91 123456789"  # Replace with the user's WhatsApp number
    # send_whatsapp_notification(message, recipient_number)
    
    # Update the last notification date
    last_notification_date = today_date

    flash("Notifications sent successfully!", "success")
    return redirect(url_for('fee_dashboard'))
    

    
def schedule_notifications():
    """
    Schedule the send_notifications function to run daily at 8:00 AM IST.
    """
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))  # Set timezone to IST
    scheduler.add_job(func=send_notifications, trigger=CronTrigger(hour=8, minute=0))  # Run at 8:00 AM IST
    scheduler.start()
    



if __name__ == '__main__':
    schedule_notifications()
    app.run(debug=True)
