from decimal import Decimal


def to_paise(amount):
    return int(round(Decimal(str(amount)) * 100))


def calculate_balances(group):
    balances = {m: {"total_paid": 0, "total_share": 0, "net_balance": 0} for m in group["members"]}
    for exp in group["expenses"]:
        if exp.get("status", "paid") != "paid":
            continue
        payer = exp["paid_by"]
        if payer in balances:
            balances[payer]["total_paid"] += to_paise(exp["amount"])
        for member, share in exp["shares"].items():
            if member in balances:
                balances[member]["total_share"] += to_paise(share)
    for m, d in balances.items():
        d["net_balance"] = d["total_paid"] - d["total_share"]
    return balances


def show_balances(group):
    print("\n========== MEMBER BALANCES ==========")
    balances = calculate_balances(group)
    if not balances:
        print("No members available.")
        return

    print(f"{'Member':<15}{'Paid':>12}{'Share':>12}{'Balance':>12}  Status")
    for member, d in balances.items():
        paid, share, bal = d["total_paid"] / 100, d["total_share"] / 100, d["net_balance"] / 100
        status = "Gets Back" if bal > 0 else ("Owes" if bal < 0 else "Settled")
        print(f"{member:<15}{paid:>12.2f}{share:>12.2f}{bal:>12.2f}  {status}")

    unpaid = [e for e in group["expenses"] if e.get("status", "paid") == "unpaid"]
    unpaid_total = sum(to_paise(e["amount"]) for e in unpaid)
    print(f"\nOutstanding unpaid expenses: Rs. {unpaid_total / 100:.2f}")
    if unpaid:
        unpaid_shares = {}
        for exp in unpaid:
            for m, s in exp["shares"].items():
                unpaid_shares[m] = unpaid_shares.get(m, 0) + to_paise(s)
        print("Outstanding shares by member:")
        for m, s_paise in unpaid_shares.items():
            print(f"  - {m}: Rs. {s_paise / 100:.2f}")


def find_optimal_settlement_plan(net_balances, is_paise=True):
    active = [(m, b) for m, b in net_balances.items() if b != 0]
    n = len(active)
    if not active:
        return []

    # Partition active members into max zero-sum subsets
    if n <= 16:
        mask_sum = [0] * (1 << n)
        for i in range(n):
            bit, bal = 1 << i, active[i][1]
            for m in range(bit):
                mask_sum[m | bit] = mask_sum[m] + bal

        zero_masks = [m for m in range(1, 1 << n) if mask_sum[m] == 0]
        memo = {}

        def backtrack(rem_mask):
            if rem_mask == 0:
                return 0, []
            if rem_mask in memo:
                return memo[rem_mask]
            lowest_bit = rem_mask & -rem_mask
            best_count, best_partition = -1, []
            for zm in zero_masks:
                if (zm & lowest_bit) and ((zm & rem_mask) == zm):
                    sub_count, sub_part = backtrack(rem_mask ^ zm)
                    if sub_count != -1 and sub_count + 1 > best_count:
                        best_count, best_partition = sub_count + 1, [zm] + sub_part
            memo[rem_mask] = (best_count, best_partition)
            return memo[rem_mask]

        max_subsets, partitions = backtrack((1 << n) - 1)
        subsets = [[active[i] for i in range(n) if (mask & (1 << i))] for mask in partitions] if max_subsets != -1 else [active]
    else:
        subsets = [active]

    transactions = []
    for subset in subsets:
        creditors = sorted([[m, b] for m, b in subset if b > 0], key=lambda x: x[1], reverse=True)
        debtors = sorted([[m, abs(b)] for m, b in subset if b < 0], key=lambda x: x[1], reverse=True)
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            debtor, d_bal = debtors[i]
            creditor, c_bal = creditors[j]
            payment = min(d_bal, c_bal)
            transactions.append({
                "debtor": debtor,
                "creditor": creditor,
                "amount": round(payment / 100, 2) if is_paise else payment
            })
            debtors[i][1] -= payment
            creditors[j][1] -= payment
            if debtors[i][1] == 0:
                i += 1
            if creditors[j][1] == 0:
                j += 1
    return transactions


def generate_settlement(group):
    print("\n========== SETTLEMENT PLAN ==========")
    balances = calculate_balances(group)
    transactions = find_optimal_settlement_plan({m: d["net_balance"] for m, d in balances.items()}, is_paise=True)
    if not transactions:
        print("No settlement required.")
        return []

    for idx, tx in enumerate(transactions, 1):
        print(f"{idx}. {tx['debtor']} pays {tx['creditor']} Rs. {tx['amount']:.2f}")

    print(f"\nAll paid-expense balances settled.\nTotal transactions: {len(transactions)}")
    unpaid_count = sum(1 for e in group["expenses"] if e.get("status", "paid") == "unpaid")
    if unpaid_count:
        print(f"Note: {unpaid_count} unpaid expense(s) are excluded from this settlement.")
    return transactions


def check_consistency(group):
    print("\n========== CONSISTENCY CHECK ==========")
    total_paid = total_shares = share_errors = 0
    for exp in group["expenses"]:
        amt = to_paise(exp["amount"])
        shares = sum(to_paise(s) for s in exp["shares"].values())
        if shares != amt:
            share_errors += 1
        if exp.get("status", "paid") == "paid":
            total_paid += amt
            total_shares += shares

    balances = calculate_balances(group)
    balance_sum = sum(d["net_balance"] for d in balances.values())
    unpaid_total = sum(to_paise(e["amount"]) for e in group["expenses"] if e.get("status", "paid") == "unpaid")

    print(f"Total paid: Rs. {total_paid / 100:.2f}\nTotal paid shares: Rs. {total_shares / 100:.2f}")
    print(f"Sum of net balances: Rs. {balance_sum / 100:.2f}\nTotal unpaid expenses: Rs. {unpaid_total / 100:.2f}")

    if total_paid == total_shares and balance_sum == 0 and share_errors == 0:
        print("\nRecords are consistent.")
        return True

    print("\nRecords are not consistent.")
    if share_errors:
        print("Some expense shares do not match their expense totals.")
    if total_paid != total_shares:
        print("Total paid and total shares do not match.")
    if balance_sum != 0:
        print("Net balances do not add up to zero.")
    return False


def minimize_transactions(group):
    return generate_settlement(group)
