from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def calculate_payment_date(joining_date):
    """
    Calculate the current month's payment date based on the joining date.
    If the joining day (e.g., 21) exceeds the number of days in the current month,
    the payment date is adjusted to the last day of the month.

    :param joining_date: Joining date as a datetime.date object
    :return: Computed payment date as a datetime.date object
    """
    try:
        # Ensure joining_date is a datetime.date object
        if isinstance(joining_date, str):
            joining_date = datetime.strptime(joining_date, "%Y-%m-%d").date()

        # Get the current date and the start of the current month
        today = date.today()
        current_month_start = today.replace(day=1)

        # Calculate the payment date within the current month
        payment_date = current_month_start + relativedelta(day=joining_date.day)

        # Handle cases where the payment day exceeds the number of days in the current month
        if payment_date.month != today.month:
            # Adjust to the last day of the current month in case of overflow
            payment_date = payment_date - relativedelta(days=payment_date.day)

        return payment_date

    except Exception as e:
        print(f"Error calculating payment date: {e}")
        return None