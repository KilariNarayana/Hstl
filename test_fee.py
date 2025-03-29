from fee import calculate_payment_date

def test_calculate_payment_date():
    test_cases = [
        "2025-01-15",  # Mid-month joining date
        "2025-02-28",  # End of February (non-leap year)
        "2024-02-29",  # End of February (leap year)
        "2025-03-31",  # End of March
        "2025-04-30",  # End of April
        "2025-05-01",  # Start of May
        "2025-06-15",  # Mid-month joining date
        "2025-07-31",  # End of July
        "2025-08-30",  # End of August
        "2025-09-15",  # Mid-month joining date
        "2025-10-31",  # End of October
        "2025-11-30",  # End of November
        "2025-12-15",  # Mid-month joining date
    ]

    for joining_date in test_cases:
        payment_date = calculate_payment_date(joining_date)
        print(f"Joining Date: {joining_date} -> Payment Date: {payment_date}")

if __name__ == "__main__":
    test_calculate_payment_date()