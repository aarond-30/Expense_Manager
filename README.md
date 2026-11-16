# EvenSplit – Group Expense Settlement Optimiser

B.Tech Capstone Project  
Problem ID: CP-007  
Language: Python 3  

A console application to manage group expenses, split bills, record repayments, and generate settlement plans with the minimum number of payments.

## Features

- **Group & Member Management:** Create groups, add members, and remove members safely.
- **Expense Tracking:** Add paid expenses, unpaid expenses, and direct repayments between members.
- **Split Options:** Split equally (with paise remainder distribution) or custom amounts.
- **Balance Calculation:** Computes net balances (`Total Paid - Total Share`) in integer paise.
- **Minimum Payment Settlement (CP-007):** Partitions balances into zero-sum subsets to find the minimum number of transactions to clear all debts.
- **Data Consistency:** Verifies total paid equals total shares and net balances sum to zero.

## Project Structure

- `expense_manager.py` - Manages groups, members, expenses, and repayments.
- `balance_settlement.py` - Calculates balances and generates settlement plans.
- `main.py` - Menu-driven interface for the application.
- `test_expense.py` - Unit tests for splits, balances, and CP-007 test cases.

## How to Run

Run the application:
```bash
python main.py
```

Run unit tests:
```bash
python -m unittest discover -v
```
