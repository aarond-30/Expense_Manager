from decimal import Decimal, InvalidOperation


def select_member(members, prompt="Select member: "):
    for i, m in enumerate(members, 1):
        print(f"{i} {m}")
    while True:
        try:
            choice = int(input(prompt))
            if 1 <= choice <= len(members):
                return members[choice - 1]
            print("Invalid selection.")
        except ValueError:
            print("Enter a valid number.")


def create_group():
    print("\n========== CREATE GROUP ==========")
    name = input("Enter group name: ").strip()
    while not name:
        print("Group name cannot be empty.")
        name = input("Enter group name: ").strip()

    group = {"group_name": name, "members": [], "expenses": []}

    while True:
        try:
            count = int(input("Enter number of members: "))
            if count > 0:
                break
            print("Enter at least one member.")
        except ValueError:
            print("Enter a valid number.")

    for _ in range(count):
        add_member(group)

    print("\nGroup created successfully!")
    return group


def add_member(group):
    while True:
        name = input("Enter member name: ").strip()
        if not name:
            print("Name cannot be empty.")
            continue
        if any(m.lower() == name.lower() for m in group["members"]):
            print("Member already exists.")
            continue
        group["members"].append(name)
        print(f"{name} added successfully.")
        return


def remove_member(group):
    if not group["members"]:
        print("No members available.")
        return
    member = select_member(group["members"], "Select member to remove: ")
    for exp in group["expenses"]:
        if (
            member in exp.get("participants", [])
            or exp.get("paid_by") == member
            or member in exp.get("shares", {})
        ):
            print("Cannot remove a member with recorded expenses.")
            return
    group["members"].remove(member)
    print(f"{member} removed successfully.")


def get_amount():
    while True:
        try:
            val = Decimal(input("Enter amount (Rs.): ").strip())
            if not val.is_finite() or val <= 0:
                print("Amount must be greater than zero.")
                continue
            if val != val.quantize(Decimal("0.01")):
                print("Enter maximum two decimal places.")
                continue
            return round(float(val), 2)
        except InvalidOperation:
            print("Enter a valid amount.")


def select_participants(group):
    print("\nSelect participants:")
    for i, m in enumerate(group["members"], 1):
        print(f"{i} {m}")
    while True:
        try:
            raw = input("Enter member numbers separated by commas: ")
            nums = [int(x.strip()) for x in raw.split(",")]
            if not nums or len(nums) != len(set(nums)):
                print("Select members without duplicates.")
                continue
            if any(n < 1 or n > len(group["members"]) for n in nums):
                print("Invalid member selection.")
                continue
            return [group["members"][n - 1] for n in nums]
        except ValueError:
            print("Enter valid member numbers.")


def create_shares(amount, participants, split_type=None, custom_amounts=None):
    total_paise = int(round(Decimal(str(amount)) * 100))
    if split_type is None:
        print("\n1. Equal split\n2. Custom split")
        while True:
            try:
                choice = int(input("Choose split type: "))
                if choice in (1, 2):
                    break
                print("Select 1 or 2.")
            except ValueError:
                print("Enter a valid number.")
    else:
        choice = split_type

    shares = {}
    if choice == 1:
        base = total_paise // len(participants)
        rem = total_paise % len(participants)
        for i, m in enumerate(participants):
            shares[m] = round((base + (1 if i < rem else 0)) / 100, 2)
    else:
        remaining = total_paise
        if custom_amounts is not None:
            for m in participants[:-1]:
                val = Decimal(str(custom_amounts.get(m, 0)))
                paise = int(round(val * 100))
                shares[m] = round(paise / 100, 2)
                remaining -= paise
            shares[participants[-1]] = round(remaining / 100, 2)
        else:
            for m in participants[:-1]:
                while True:
                    try:
                        v = Decimal(input(f"Share for {m}: ").strip())
                        if not v.is_finite() or v < 0:
                            print("Enter a valid non-negative amount.")
                            continue
                        if v != v.quantize(Decimal("0.01")):
                            print("Enter maximum two decimal places.")
                            continue
                        paise = int(round(v * 100))
                        if paise > remaining:
                            print("Share exceeds the remaining amount.")
                            continue
                        shares[m] = round(paise / 100, 2)
                        remaining -= paise
                        break
                    except InvalidOperation:
                        print("Enter a valid amount.")
            shares[participants[-1]] = round(remaining / 100, 2)
            print(f"{participants[-1]} remaining share: {remaining / 100:.2f}")
    return shares


def record_expense(group, status):
    if not group["members"]:
        print("Add members first.")
        return
    desc = input("Enter expense description: ").strip()
    while not desc:
        print("Description cannot be empty.")
        desc = input("Enter expense description: ").strip()

    amount = get_amount()
    participants = select_participants(group)
    shares = create_shares(amount, participants)
    paid_by = None

    if status == "paid":
        print("\nSelect payer:")
        paid_by = select_member(group["members"], "Select payer: ")

    group["expenses"].append({
        "description": desc,
        "amount": amount,
        "paid_by": paid_by,
        "participants": participants,
        "shares": shares,
        "status": status
    })
    print("\nExpense recorded successfully.")
    print(f"Description: {desc}")
    print(f"Amount: Rs. {amount:.2f}")
    print(f"Status: {status.upper()}")


def add_expense(group):
    print("\n========== ADD PAID EXPENSE ==========")
    record_expense(group, "paid")


def add_unpaid_expense(group):
    print("\n========== ADD UNPAID EXPENSE ==========")
    record_expense(group, "unpaid")


def record_repayment(group, payer=None, recipient=None, amount=None, note=None):
    if len(group["members"]) < 2:
        print("At least two members are required for repayment.")
        return None

    if payer is None:
        print("\n========== RECORD REPAYMENT ==========")
        print("Select payer (who is paying):")
        selected_payer = select_member(group["members"], "Select payer: ")
    else:
        selected_payer = payer

    recipients = [m for m in group["members"] if m != selected_payer]

    if recipient is None:
        print("\nSelect recipient (who is receiving):")
        selected_recipient = select_member(recipients, "Select recipient: ")
    else:
        selected_recipient = recipient

    selected_amount = get_amount() if amount is None else round(float(amount), 2)

    if payer is None:
        default_note = f"Repayment from {selected_payer} to {selected_recipient}"
        raw_note = input(f"Enter note/description (default: {default_note}): ").strip()
        description = raw_note if raw_note else default_note
    else:
        description = note if note else f"Repayment from {selected_payer} to {selected_recipient}"

    expense = {
        "description": description,
        "amount": selected_amount,
        "paid_by": selected_payer,
        "participants": [selected_recipient],
        "shares": {selected_recipient: selected_amount},
        "status": "paid"
    }
    group["expenses"].append(expense)
    print("\nRepayment recorded successfully.")
    print(f"{selected_payer} paid {selected_recipient} Rs. {selected_amount:.2f}")
    return expense


def repay(group, payer=None, recipient=None, amount=None, note=None):
    return record_repayment(group, payer, recipient, amount, note)


def mark_expense_paid(group):
    unpaid = [e for e in group["expenses"] if e.get("status", "paid") == "unpaid"]
    if not unpaid:
        print("No unpaid expenses.")
        return

    print("\n========== UNPAID EXPENSES ==========")
    for i, e in enumerate(unpaid, 1):
        print(f"{i} {e['description']} - Rs. {e['amount']:.2f}")

    while True:
        try:
            choice = int(input("Select expense to mark as paid: "))
            if 1 <= choice <= len(unpaid):
                break
            print("Invalid selection.")
        except ValueError:
            print("Enter a valid number.")

    expense = unpaid[choice - 1]
    print("\nSelect the person who paid:")
    expense["paid_by"] = select_member(group["members"], "Select payer: ")
    expense["status"] = "paid"
    print("\nExpense marked as paid successfully.")
    print(f"Paid by: {expense['paid_by']}")


def show_unpaid_expenses(group):
    print("\n========== UNPAID EXPENSES ==========")
    unpaid = [e for e in group["expenses"] if e.get("status", "paid") == "unpaid"]
    if not unpaid:
        print("No unpaid expenses.")
        return
    for i, exp in enumerate(unpaid, 1):
        print(f"\nExpense: {i}")
        print(f"Description: {exp['description']}")
        print(f"Amount: Rs. {exp['amount']:.2f}")
        for member, share in exp["shares"].items():
            print(f"{member} owes: {share:.2f}")


def delete_expense(group):
    if not group["expenses"]:
        print("No expenses available.")
        return
    show_expense_history(group)
    while True:
        try:
            choice = int(input("Enter expense number to delete: "))
            if 1 <= choice <= len(group["expenses"]):
                break
            print("Invalid selection.")
        except ValueError:
            print("Enter a valid number.")
    removed = group["expenses"].pop(choice - 1)
    print(f"{removed['description']} deleted successfully.")


def show_expense_history(group):
    print("\n========== EXPENSE HISTORY ==========")
    print(f"Group: {group['group_name']}")
    if not group["expenses"]:
        print("No expenses recorded.")
        return
    for i, exp in enumerate(group["expenses"], 1):
        print(f"\nExpense: {i}")
        print(f"Description: {exp['description']}")
        print(f"Amount: Rs. {exp['amount']:.2f}")
        print(f"Status: {exp.get('status', 'paid').upper()}")
        print(f"Paid by: {exp['paid_by'] or 'Nobody yet'}")
        print("Participants:")
        for m in exp["participants"]:
            print(f"- {m}")
        print("Shares:")
        for m, s in exp["shares"].items():
            print(f"{m} : {s:.2f}")
