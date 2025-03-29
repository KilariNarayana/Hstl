test_data = [
    {
        "member_id": 1,
        "name": "John Doe",
        "room_number": "101",
        "fee_amount": 5000,
        "payment_paid_amount": 5000,  # Fully paid
        "previous_month_balance": 0,  # No balance
        "expected_previous_month_balance": 0,  # Should remain 0
    },
    {
        "member_id": 2,
        "name": "Jane Smith",
        "room_number": "102",
        "fee_amount": 5000,
        "payment_paid_amount": 3000,  # Partially paid
        "previous_month_balance": 0,  # No balance initially
        "expected_previous_month_balance": 2000,  # Remaining balance should be carried forward
    },
    {
        "member_id": 3,
        "name": "Alice Johnson",
        "room_number": "103",
        "fee_amount": 5000,
        "payment_paid_amount": 0,  # Not paid
        "previous_month_balance": 0,  # No balance initially
        "expected_previous_month_balance": 5000,  # Full fee amount should be carried forward
    },
    {
        "member_id": 4,
        "name": "Bob Brown",
        "room_number": "104",
        "fee_amount": 5000,
        "payment_paid_amount": 7000,  # Overpaid (covers previous balance)
        "previous_month_balance": 2000,  # Balance carried forward
        "expected_previous_month_balance": 0,  # Should reset to 0
    },
]


def test_previous_month_balance_logic():
    for test_case in test_data:
        # Extract test case details
        member_id = test_case["member_id"]
        name = test_case["name"]
        room_number = test_case["room_number"]
        fee_amount = test_case["fee_amount"]
        payment_paid_amount = test_case["payment_paid_amount"]
        previous_month_balance = test_case["previous_month_balance"]
        expected_previous_month_balance = test_case["expected_previous_month_balance"]

        # Calculate the remaining balance for the previous month
        remaining_balance = fee_amount - payment_paid_amount
        if remaining_balance < 0:
            remaining_balance = 0  # No negative balances

        # Update the previous_month_balance for the current month
        if remaining_balance > 0:
            current_previous_month_balance = remaining_balance
        else:
            current_previous_month_balance = 0

        # Assert the result
        assert current_previous_month_balance == expected_previous_month_balance, (
            f"Test failed for member {name} (ID: {member_id}). "
            f"Expected previous_month_balance: {expected_previous_month_balance}, "
            f"Got: {current_previous_month_balance}"
        )

        print(f"Test passed for member {name} (ID: {member_id}).")

# Run the test
test_previous_month_balance_logic()