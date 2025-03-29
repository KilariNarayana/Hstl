import schedule
import time
from threading import Thread
from twilio.rest import Client
from data_handler import read_data


# Twilio configuration
TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'


# Function to send SMS
def send_sms(to_phone_number, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        print(f"SMS sent to {to_phone_number}")
    except Exception as e:
        print(f"Failed to send SMS to {to_phone_number}: {e}")


# Function to send reminders to users with unpaid fees
def send_fee_reminders():
    members, _ = read_data()
    for member in members:
        if member['Fee Paid'] != 'Yes':
            message = f"Dear {member['Name']}, your hostel fee is overdue. Please pay it immediately."
            send_sms(member['Phone Number'], message)


# Function to schedule daily tasks like fee reminders
schedule.every().day.at("08:00").do(send_fee_reminders)


# Function to run the scheduled jobs in a loop
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep