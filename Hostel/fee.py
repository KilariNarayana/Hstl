from datetime import datetime
from dateutil.relativedelta import relativedelta



def calculate_payment_date(joining_date):
    """
    Calculate the current month's payment date based on the joining date.
    If the joining day (e.g., 21) exceeds the number of days in the current month,
    the payment date is adjusted to the last day of the month.

    :param joining_date: Joining date as a string (YYYY-MM-DD)
    :return: Computed payment date as a string (YYYY-MM-DD)
    """
    try:
        # Convert joining_date to a datetime object
        joining_date = datetime.strptime(joining_date, "%Y-%m-%d")

        # Get the current date and the start of the current month
        today = datetime.today()
        current_month_start = today.replace(day=1)

        # Calculate the payment date within the current month
        payment_date = current_month_start + relativedelta(day=joining_date.day)

        # Handle cases where the payment day exceeds the number of days in the current month
        if payment_date.month != today.month:
            # Adjust to the last day of the current month in case of overflow
            payment_date = payment_date - relativedelta(days=payment_date.day)

        return payment_date.strftime("%Y-%m-%d")

    except Exception as e:
        print(f"Error calculating payment date: {e}")
        return None