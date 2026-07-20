# 📚 Library Management System

A mini project demonstrating a full-stack application built with **MySQL** (backend database) and **Python + Streamlit** (frontend), covering DDL, DML, DQL, DCL, TCL, stored procedures, functions, and triggers.

---

## Problem Statement

Manual library record-keeping — issuing books, tracking returns, and calculating overdue fines — is slow and error-prone. This project automates these operations using a MySQL database as the backend, with a Streamlit web app as the user interface, and a reusable Python class (`connectDB`) as the data-access layer.

**Key goals:**
- Maintain records of books, categories, members, and staff
- Issue and return books, with automatic due-date tracking
- Automatically calculate overdue fines using database-side logic
- Provide reports (available books, transaction history, unpaid fines)
- Demonstrate core SQL concepts (DDL, DML, DQL, DCL, TCL) plus a stored procedure, function, and trigger

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | MySQL 8.x |
| Backend / Data Access | Python 3, `mysql-connector-python` |
| Frontend | Streamlit |
| Data handling | pandas |

---

## Database Design (ER Overview)

| Table | Key Columns | Notes |
|---|---|---|
| **Category** | `category_id` (PK), `category_name` | Book categories |
| **Books** | `book_id` (PK), `title`, `author`, `category_id` (FK), `isbn`, `total_copies`, `available_copies`, `price` | |
| **Members** | `member_id` (PK), `name`, `email`, `phone`, `address`, `password`, `membership_date` | Library members / students |
| **Staff** | `staff_id` (PK), `name`, `email`, `role`, `password` | Librarians / admins |
| **Transactions** | `transaction_id` (PK), `book_id` (FK), `member_id` (FK), `staff_id` (FK), `issue_date`, `due_date`, `return_date`, `status` | One row per book issue/return |
| **Fine** | `fine_id` (PK), `transaction_id` (FK), `amount`, `paid_status` | Auto-populated by trigger on return |

**Business rule:** due date = issue date + 14 days; fine = ₹5/day beyond due date.

---

## SQL Concepts Covered (`library_management.sql`)

- **DDL** — `CREATE DATABASE`, `CREATE TABLE` (PK/FK/CHECK constraints), `ALTER TABLE`
- **DML** — `INSERT`, `UPDATE`, `DELETE`
- **DQL** — `SELECT` with `JOIN`, `GROUP BY`, aggregate functions, subqueries
- **DCL** — `CREATE USER`, `GRANT`, `REVOKE`
- **TCL** — `START TRANSACTION`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`
- **Stored Procedure** — `sp_IssueBook`: checks copy availability, inserts a transaction, decrements `available_copies`
- **Function** — `fn_CalculateFine`: computes fine based on days overdue
- **Trigger** — `trg_AfterReturn`: on book return, restores `available_copies` and auto-inserts the fine record via `fn_CalculateFine`

---

## Project Structure

```
├── library_management.sql   # Full database schema, seed data, procedure/function/trigger
├── connectDB.py             # Reusable class for connecting to MySQL and running queries
├── main.py                  # Streamlit front-end (Member / Admin / Registration)
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <repo-folder>
```

### 2. Set up the database
Import the schema into MySQL:
```bash
mysql -u root -p < library_management.sql
```
This creates the `library_management` database, all tables, seed data, the stored procedure, function, and trigger.

### 3. Install Python dependencies
```bash
pip install streamlit mysql-connector-python pandas
```

### 4. Configure your database credentials
Open `main.py` and update the `DB_CONFIG` dictionary near the top with your MySQL username/password:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "library_management",
}
```

### 5. Run the app
```bash
streamlit run main.py
```
The app opens in your browser at `http://localhost:8501`.

---

## Sample Login Credentials (from seed data)

| Role | ID | Password |
|---|---|---|
| Member | `1` | `priya123` |
| Member | `2` | `aman123` |
| Admin/Staff | *(check `Staff` table password column — set your own hash/value or update `sp_IssueBook`'s hardcoded `staff_id=1`)* | — |

> Note: passwords are stored in plain text in this schema for simplicity. In a production system, always hash passwords (e.g. with `bcrypt`) before storing them.

---

## Features

**Member**
- Login
- View all books
- Issue a book (calls `sp_IssueBook` stored procedure)
- View currently issued books
- Return a book (fires `trg_AfterReturn`, auto-calculates fine if overdue)

**Admin / Staff**
- Login
- View all transactions
- Add a new book
- Delete a book *(blocked by a foreign key constraint if the book has transaction history — by design, to preserve data integrity)*
- View unpaid fines

**Registration**
- New members can self-register

---

## Notes / Known Constraints

- `sp_IssueBook` currently logs the issuing staff as `staff_id = 1` — make sure at least one row exists in the `Staff` table.
- Deleting a book with existing transaction history is intentionally blocked by MySQL's foreign key constraint (`fk_txn_book`) to avoid orphaned records.
- This is an educational mini project; production hardening (password hashing, connection pooling, input validation, HTTPS) is out of scope but noted here for anyone extending it.

---

## License

This project was created for academic/educational purposes as a mini project.
