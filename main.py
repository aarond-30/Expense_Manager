from expense_manager import (
    create_group,
    add_member,
    remove_member,
    add_expense,
    add_unpaid_expense,
    record_repayment,
    mark_expense_paid,
    show_unpaid_expenses,
    delete_expense,
    show_expense_history
)
from balance_settlement import (
    show_balances,
    generate_settlement,
    check_consistency
)


def main():
    group = None

    while True:
        print("\n========== EVENSPLIT ==========")
        print("1. Create Group")
        print("2. Add Member")
        print("3. Add Expense")
        print("4. View Expenses")
        print("5. View Balances")
        print("6. Settle Expenses")
        print("7. Check Records")
        print("8. Exit")
        print("================================")

        try:
            choice = int(input("\nEnter your choice: "))
        except ValueError:
            print("Enter a valid menu number.")
            continue

        if choice == 1:
            if group is not None:
                confirm = input("Replace existing group? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    continue
            group = create_group()

        elif choice == 8:
            print("\nThank you for using EvenSplit!")
            break

        elif choice in range(2, 8):
            if group is None:
                print("Please create a group first.")
                continue

            if choice == 2:
                print("\n1. Add Member\n2. Remove Member")
                sub = input("Enter choice (1/2): ").strip()
                if sub == "2":
                    remove_member(group)
                elif sub in ["1", ""]:
                    add_member(group)
                else:
                    print("Invalid choice.")

            elif choice == 3:
                print("\n1. Add Paid Expense\n2. Add Unpaid Expense\n3. Record Repayment")
                sub = input("Enter choice (1/2/3): ").strip()
                if sub == "1":
                    add_expense(group)
                elif sub == "2":
                    add_unpaid_expense(group)
                elif sub == "3":
                    record_repayment(group)
                else:
                    print("Invalid choice.")

            elif choice == 4:
                print("\n1. View Expense History\n2. View Unpaid Expenses\n3. Delete Expense")
                sub = input("Enter choice (1/2/3): ").strip()
                if sub == "1":
                    show_expense_history(group)
                elif sub == "2":
                    show_unpaid_expenses(group)
                elif sub == "3":
                    delete_expense(group)
                else:
                    print("Invalid choice.")

            elif choice == 5:
                show_balances(group)

            elif choice == 6:
                print("\n1. Record Repayment\n2. Mark Expense as Paid\n3. Generate Settlement Plan")
                sub = input("Enter choice (1/2/3): ").strip()
                if sub == "1":
                    record_repayment(group)
                elif sub == "2":
                    mark_expense_paid(group)
                elif sub == "3":
                    generate_settlement(group)
                else:
                    print("Invalid choice.")

            elif choice == 7:
                check_consistency(group)
        else:
            print("Invalid choice. Select between 1 and 8.")


if __name__ == "__main__":
    main()
