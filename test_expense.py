import unittest
from decimal import Decimal
from expense_manager import create_shares, remove_member, record_repayment, repay
from balance_settlement import (
    calculate_balances,
    generate_settlement,
    check_consistency,
    to_paise,
    minimize_transactions,
    find_optimal_settlement_plan
)


class TestCP007MinimumPayments(unittest.TestCase):

    def verify_settlement(self, balances, txs):
        total_credit = sum(b for b in balances.values() if b > 0)
        total_debt = sum(abs(b) for b in balances.values() if b < 0)
        self.assertEqual(total_credit, total_debt)

        net_change = {m: 0 for m in balances}
        for tx in txs:
            self.assertNotEqual(tx["debtor"], tx["creditor"])
            self.assertGreater(tx["amount"], 0)
            net_change[tx["debtor"]] += tx["amount"]
            net_change[tx["creditor"]] -= tx["amount"]

        for member, bal in balances.items():
            self.assertEqual(bal + net_change[member], 0)
        self.assertEqual(sum(tx["amount"] for tx in txs), total_credit)

    def test_cp007_case_1(self):
        bal = {"A": 2000, "B": -1200, "C": -800}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 2)
        self.verify_settlement(bal, txs)

    def test_cp007_case_2(self):
        bal = {"A": 1000, "B": 1000, "C": -2000}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 2)
        self.verify_settlement(bal, txs)

    def test_cp007_case_3(self):
        bal = {"A": 3000, "B": -1000, "C": -1000, "D": -1000}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 3)
        self.verify_settlement(bal, txs)

    def test_cp007_case_4(self):
        bal = {"A": 2000, "B": 2000, "C": -1000, "D": -1000, "E": -2000}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 3)
        self.verify_settlement(bal, txs)

    def test_cp007_case_5(self):
        bal = {"A": 1000, "B": -1000}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 1)
        self.verify_settlement(bal, txs)

    def test_cp007_case_6(self):
        bal = {"A": 0, "B": 0, "C": 0}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 0)

    def test_cp007_case_7(self):
        bal = {"A": 1500, "B": -500, "C": -500, "D": -500}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 3)
        self.verify_settlement(bal, txs)

    def test_optimal_beats_greedy_counterexample(self):
        bal = {"A": 4000, "B": 3000, "C": 2000, "D": -5000, "E": -4000}
        txs = find_optimal_settlement_plan(bal, is_paise=False)
        self.assertEqual(len(txs), 3)
        self.verify_settlement(bal, txs)


class TestExpense(unittest.TestCase):

    def test_01_two_members_sharing_equally(self):
        shares = create_shares(1000.0, ["Aaron", "Amosh"], split_type=1)
        self.assertEqual(shares["Aaron"], 500.0)
        self.assertEqual(shares["Amosh"], 500.0)
        group = {
            "group_name": "Trip",
            "members": ["Aaron", "Amosh"],
            "expenses": [{
                "description": "Hotel",
                "amount": 1000.0,
                "paid_by": "Aaron",
                "participants": ["Aaron", "Amosh"],
                "shares": shares,
                "status": "paid"
            }]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 50000)
        self.assertEqual(balances["Amosh"]["net_balance"], -50000)
        txs = generate_settlement(group)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["debtor"], "Amosh")
        self.assertEqual(txs[0]["creditor"], "Aaron")
        self.assertTrue(check_consistency(group))

    def test_02_three_members_sharing_equally(self):
        shares = create_shares(100.0, ["Aaron", "Amosh", "Rahul"], split_type=1)
        self.assertEqual(shares["Aaron"], 33.34)
        self.assertEqual(shares["Amosh"], 33.33)
        self.assertEqual(shares["Rahul"], 33.33)
        self.assertEqual(sum(to_paise(s) for s in shares.values()), to_paise(100.0))
        group = {
            "group_name": "Flat",
            "members": ["Aaron", "Amosh", "Rahul"],
            "expenses": [{
                "description": "Groceries",
                "amount": 100.0,
                "paid_by": "Aaron",
                "participants": ["Aaron", "Amosh", "Rahul"],
                "shares": shares,
                "status": "paid"
            }]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 6666)
        self.assertEqual(balances["Amosh"]["net_balance"], -3333)
        self.assertTrue(check_consistency(group))

    def test_03_one_member_paying_for_everyone(self):
        members = ["Alice", "Bob", "Charlie", "David"]
        group = {
            "group_name": "Dinner",
            "members": members,
            "expenses": [{
                "description": "Dinner Bill",
                "amount": 200.0,
                "paid_by": "Alice",
                "participants": members,
                "shares": create_shares(200.0, members, split_type=1),
                "status": "paid"
            }]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Alice"]["net_balance"], 15000)
        txs = generate_settlement(group)
        self.assertEqual(len(txs), 3)
        self.assertTrue(check_consistency(group))

    def test_04_multiple_members_paying_different_expenses(self):
        group = {
            "group_name": "Vacation",
            "members": ["Alice", "Bob", "Charlie"],
            "expenses": [
                {"description": "Travel", "amount": 300.0, "paid_by": "Alice", "participants": ["Alice", "Bob", "Charlie"], "shares": {"Alice": 100.0, "Bob": 100.0, "Charlie": 100.0}, "status": "paid"},
                {"description": "Food", "amount": 150.0, "paid_by": "Bob", "participants": ["Alice", "Bob", "Charlie"], "shares": {"Alice": 50.0, "Bob": 50.0, "Charlie": 50.0}, "status": "paid"},
                {"description": "Snacks", "amount": 90.0, "paid_by": "Charlie", "participants": ["Alice", "Bob"], "shares": {"Alice": 45.0, "Bob": 45.0}, "status": "paid"}
            ]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Alice"]["net_balance"], 10500)
        self.assertEqual(balances["Bob"]["net_balance"], -4500)
        self.assertEqual(balances["Charlie"]["net_balance"], -6000)
        txs = generate_settlement(group)
        self.assertEqual(len(txs), 2)
        self.assertTrue(check_consistency(group))

    def test_05_custom_expense_splitting(self):
        shares = create_shares(250.0, ["Aaron", "Amosh", "Rahul"], split_type=2, custom_amounts={"Aaron": 100.0, "Amosh": 75.0})
        self.assertEqual(shares["Aaron"], 100.0)
        self.assertEqual(shares["Amosh"], 75.0)
        self.assertEqual(shares["Rahul"], 75.0)
        group = {
            "group_name": "Project",
            "members": ["Aaron", "Amosh", "Rahul"],
            "expenses": [{"description": "Components", "amount": 250.0, "paid_by": "Aaron", "participants": ["Aaron", "Amosh", "Rahul"], "shares": shares, "status": "paid"}]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 15000)
        self.assertEqual(balances["Amosh"]["net_balance"], -7500)
        self.assertTrue(check_consistency(group))

    def test_06_unpaid_expenses(self):
        group = {
            "group_name": "Hostel",
            "members": ["Aaron", "Amosh"],
            "expenses": [{"description": "Power", "amount": 500.0, "paid_by": None, "participants": ["Aaron", "Amosh"], "shares": {"Aaron": 250.0, "Amosh": 250.0}, "status": "unpaid"}]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 0)
        txs = generate_settlement(group)
        self.assertEqual(len(txs), 0)
        self.assertTrue(check_consistency(group))

    def test_07_marking_unpaid_expense_as_paid(self):
        exp = {"description": "Wifi", "amount": 600.0, "paid_by": None, "participants": ["Aaron", "Amosh"], "shares": {"Aaron": 300.0, "Amosh": 300.0}, "status": "unpaid"}
        group = {"group_name": "Hostel", "members": ["Aaron", "Amosh"], "expenses": [exp]}
        exp["paid_by"] = "Aaron"
        exp["status"] = "paid"
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 30000)
        self.assertEqual(balances["Amosh"]["net_balance"], -30000)
        txs = generate_settlement(group)
        self.assertEqual(len(txs), 1)
        self.assertTrue(check_consistency(group))

    def test_08_multiple_creditors_and_debtors_optimal(self):
        group = {
            "group_name": "Outing",
            "members": ["A", "B", "C", "D", "E"],
            "expenses": [
                {"description": "Item 1", "amount": 2000.0, "paid_by": "A", "participants": ["C", "D"], "shares": {"C": 1000.0, "D": 1000.0}, "status": "paid"},
                {"description": "Item 2", "amount": 2000.0, "paid_by": "B", "participants": ["E"], "shares": {"E": 2000.0}, "status": "paid"}
            ]
        }
        txs = generate_settlement(group)
        self.assertEqual(len(txs), 3)
        self.assertTrue(check_consistency(group))

    def test_09_all_members_having_zero_balances(self):
        group = {
            "group_name": "Lunch",
            "members": ["Aaron", "Amosh"],
            "expenses": [
                {"description": "Lunch 1", "amount": 100.0, "paid_by": "Aaron", "participants": ["Aaron", "Amosh"], "shares": {"Aaron": 50.0, "Amosh": 50.0}, "status": "paid"},
                {"description": "Lunch 2", "amount": 100.0, "paid_by": "Amosh", "participants": ["Aaron", "Amosh"], "shares": {"Aaron": 50.0, "Amosh": 50.0}, "status": "paid"}
            ]
        }
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 0)
        self.assertEqual(len(generate_settlement(group)), 0)

    def test_10_remove_member_with_recorded_expenses_blocked(self):
        group = {
            "group_name": "Test",
            "members": ["Alice", "Bob"],
            "expenses": [{"description": "Gift", "amount": 50.0, "paid_by": "Alice", "participants": ["Bob"], "shares": {"Bob": 50.0}, "status": "paid"}]
        }
        for exp in group["expenses"]:
            is_involved = "Alice" in exp.get("participants", []) or exp.get("paid_by") == "Alice" or "Alice" in exp.get("shares", {})
            self.assertTrue(is_involved)

    def test_11_decimal_amounts_and_paise_distribution(self):
        self.assertEqual(to_paise(1.15), 115)
        self.assertEqual(to_paise(2.30), 230)
        self.assertEqual(to_paise(10.05), 1005)
        shares = create_shares(10.01, ["A", "B", "C"], split_type=1)
        self.assertEqual(shares["A"], 3.34)
        self.assertEqual(shares["B"], 3.34)
        self.assertEqual(shares["C"], 3.33)
        self.assertEqual(sum(to_paise(s) for s in shares.values()), to_paise(10.01))

    def test_12_delete_expense_and_recalculate_balances(self):
        group = {
            "group_name": "Weekend",
            "members": ["Aaron", "Amosh"],
            "expenses": [
                {"description": "Exp 1", "amount": 200.0, "paid_by": "Aaron", "participants": ["Aaron", "Amosh"], "shares": {"Aaron": 100.0, "Amosh": 100.0}, "status": "paid"},
                {"description": "Exp 2", "amount": 80.0, "paid_by": "Amosh", "participants": ["Aaron", "Amosh"], "shares": {"Aaron": 40.0, "Amosh": 40.0}, "status": "paid"}
            ]
        }
        group["expenses"].pop(1)
        balances = calculate_balances(group)
        self.assertEqual(balances["Aaron"]["net_balance"], 10000)
        self.assertEqual(balances["Amosh"]["net_balance"], -10000)
        self.assertTrue(check_consistency(group))

    def test_13_record_repayment_settles_balances(self):
        group = {
            "group_name": "Flatmates",
            "members": ["Alice", "Bob"],
            "expenses": [{"description": "Bill", "amount": 1000.0, "paid_by": "Alice", "participants": ["Alice", "Bob"], "shares": {"Alice": 500.0, "Bob": 500.0}, "status": "paid"}]
        }
        record_repayment(group, payer="Bob", recipient="Alice", amount=500.0)
        balances = calculate_balances(group)
        self.assertEqual(balances["Alice"]["net_balance"], 0)
        self.assertEqual(balances["Bob"]["net_balance"], 0)
        self.assertEqual(len(generate_settlement(group)), 0)
        self.assertTrue(check_consistency(group))


def create_shares_for_test(amount, members):
    total = round(amount * 100)
    base = total // len(members)
    rem = total % len(members)
    return {m: round((base + (1 if i < rem else 0)) / 100, 2) for i, m in enumerate(members)}


if __name__ == "__main__":
    unittest.main()
