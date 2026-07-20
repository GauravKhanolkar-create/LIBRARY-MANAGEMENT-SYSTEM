import streamlit as st
import pandas as pd
import datetime
from connectDB import connectDB

st.set_page_config(page_title="Library Management System", page_icon="https://cdn-icons-png.flaticon.com/512/4318/4318379.png")
st.title("LIBRARY MANAGEMENT SYSTEM")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Your Password",
    "database": "library_management",
}


def get_db():
    """Return a connected connectDB instance, or stop the app with a clear error."""
    db = connectDB(**DB_CONFIG)
    if not db.connect():
        st.error(f"Could not connect to the database: {db.last_error}")
        st.stop()
    return db


choice = st.sidebar.selectbox("Main Menu", ("HOME", "MEMBER", "ADMIN", "REGISTRATION"))

if choice == "HOME":
    st.image("https://www.creativ-eras.com/assets/images/library-slider-img-1.jpg")
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSOa827Wbzk0dZ-itcER3TZ3PxuhMAjgmeM4eM1-Qp0Kg&s=10", width=500)
    st.write("This is a Library Management System built with MySQL and Streamlit, "
             "developed as a mini project.")

elif choice == "MEMBER":
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhJzwWcLW5A02PF9KK5wNDZ16DI6idg0d1D3y01XnJTh1PZIDIWGTcaA0&s=10", width=500)
    if "islogin" not in st.session_state:
        st.session_state['islogin'] = False
        st.session_state['member_id'] = None

    mid = st.text_input("Enter Member ID")
    pwd = st.text_input("Enter Password", type="password")
    btn = st.button("Login")

    if btn:
        db = get_db()
        data = db.fetch_query("SELECT * FROM Members WHERE member_id = %s AND password = %s", (mid, pwd))
        db.disconnect()
        if data:
            st.session_state['islogin'] = True
            st.session_state['member_id'] = int(mid)
        else:
            st.session_state['islogin'] = False
            st.subheader("Incorrect ID or Password")

    if st.session_state['islogin']:
        st.subheader("Login Successful")
        choice2 = st.selectbox("Features", ("None", "View All Books", "Issue Book", "My Issued Books", "Return Book"))

        if choice2 == "View All Books":
            db = get_db()
            data = db.fetch_query(
                "SELECT b.book_id, b.title, b.author, c.category_name, b.available_copies "
                "FROM Books b LEFT JOIN Category c ON b.category_id = c.category_id"
            )
            db.disconnect()
            df = pd.DataFrame(data)
            st.dataframe(df)

        elif choice2 == "Issue Book":
            bid = st.text_input("Enter Book ID")
            btn2 = st.button("Issue Book")
            if btn2:
                db = get_db()
                try:
                    bid_int = int(bid)
                except ValueError:
                    st.error("Book ID must be a number.")
                    db.disconnect()
                    st.stop()
                result = db.call_procedure("sp_IssueBook", (bid_int, st.session_state['member_id'], 1, ""))
                if result and len(result) > 3:
                    st.subheader(result[3])
                else:
                    st.error(f"Issue Book failed: {db.last_error or 'Unexpected response from stored procedure.'}")
                db.disconnect()

        elif choice2 == "My Issued Books":
            db = get_db()
            data = db.fetch_query(
                "SELECT t.transaction_id, b.title, t.issue_date, t.due_date, t.status "
                "FROM Transactions t JOIN Books b ON t.book_id = b.book_id "
                "WHERE t.member_id = %s", (st.session_state['member_id'],)
            )
            db.disconnect()
            df = pd.DataFrame(data)
            st.dataframe(df)

        elif choice2 == "Return Book":
            db = get_db()
            issued = db.fetch_query(
                "SELECT t.transaction_id, b.title FROM Transactions t "
                "JOIN Books b ON t.book_id = b.book_id "
                "WHERE t.member_id = %s AND t.status = 'Issued'", (st.session_state['member_id'],)
            )
            db.disconnect()
            if issued:
                options = {f"{row['transaction_id']} - {row['title']}": row['transaction_id'] for row in issued}
                selected = st.selectbox("Select Book to Return", list(options.keys()))
                btn3 = st.button("Return Book")
                if btn3:
                    db = get_db()
                    result = db.execute_query(
                        "UPDATE Transactions SET return_date = %s, status = 'Returned' WHERE transaction_id = %s",
                        (datetime.date.today(), options[selected])
                    )
                    if result:
                        fine = db.fetch_query(
                            "SELECT amount FROM Fine WHERE transaction_id = %s", (options[selected],)
                        )
                        st.subheader("Book Returned Successfully")
                        if fine and fine[0]['amount'] > 0:
                            st.warning(f"Fine incurred: Rs. {fine[0]['amount']}")
                    else:
                        st.error(f"Return Book failed: {db.last_error}")
                    db.disconnect()
            else:
                st.write("You have no books currently issued.")

elif choice == "ADMIN":
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQB0EO76Xq-bvrfYu323Twj8Z16wf72zpCHnhS-jP3rcwxVeWBJti5fCwWr&s=10", width=500)
    if "islogin2" not in st.session_state:
        st.session_state['islogin2'] = False

    sid = st.text_input("Enter Staff ID")
    pwd = st.text_input("Enter Staff Password", type="password")
    btn = st.button("Login")

    if btn:
        db = get_db()
        data = db.fetch_query("SELECT * FROM Staff WHERE staff_id = %s AND password = %s", (sid, pwd))
        db.disconnect()
        st.session_state['islogin2'] = bool(data)
        if not data:
            st.subheader("Incorrect ID or Password")

    if st.session_state['islogin2']:
        st.subheader("Login Successful")
        choice2 = st.selectbox("Features", ("None", "View All Transactions", "Add Book", "Delete Book", "View Unpaid Fines"))

        if choice2 == "View All Transactions":
            db = get_db()
            data = db.fetch_query(
                "SELECT t.transaction_id, m.name AS member, b.title AS book, "
                "t.issue_date, t.due_date, t.return_date, t.status "
                "FROM Transactions t "
                "JOIN Members m ON t.member_id = m.member_id "
                "JOIN Books b ON t.book_id = b.book_id"
            )
            db.disconnect()
            df = pd.DataFrame(data)
            st.dataframe(df)

        elif choice2 == "Add Book":
            bname = st.text_input("Enter Book Title")
            aname = st.text_input("Enter Author Name")
            isbn = st.text_input("Enter ISBN")
            copies = st.number_input("Enter Number of Copies", min_value=1, step=1)
            price = st.number_input("Enter Price", min_value=0.0, step=1.0)
            btn2 = st.button("Add Book")
            if btn2:
                db = get_db()
                result = db.execute_query(
                    "INSERT INTO Books (title, author, isbn, total_copies, available_copies, price) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (bname, aname, isbn, copies, copies, price)
                )
                if result:
                    check = db.fetch_query("SELECT * FROM Books WHERE isbn = %s", (isbn,))
                    st.subheader("Book Added Successfully")
                    st.dataframe(pd.DataFrame(check))
                else:
                    st.error(f"Add Book failed: {db.last_error}")
                db.disconnect()

        elif choice2 == "Delete Book":
            db = get_db()
            data = db.fetch_query("SELECT book_id, title FROM Books")
            db.disconnect()
            df = pd.DataFrame(data)
            if not df.empty:
                bid = st.selectbox("Choose Book ID to delete", df['book_id'])
                btn2 = st.button("Delete Book")
                if btn2:
                    db = get_db()
                    result = db.execute_query("DELETE FROM Books WHERE book_id = %s", (bid,))
                    if result:
                        st.subheader("Book Deleted Successfully")
                    else:
                        st.error(f"Delete Book failed: {db.last_error}")
                    db.disconnect()

        elif choice2 == "View Unpaid Fines":
            db = get_db()
            data = db.fetch_query(
                "SELECT f.fine_id, m.name AS member, b.title AS book, f.amount, f.paid_status "
                "FROM Fine f "
                "JOIN Transactions t ON f.transaction_id = t.transaction_id "
                "JOIN Members m ON t.member_id = m.member_id "
                "JOIN Books b ON t.book_id = b.book_id "
                "WHERE f.paid_status = 'Unpaid'"
            )
            db.disconnect()
            df = pd.DataFrame(data)
            st.dataframe(df)

elif choice == "REGISTRATION":
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ80y7K_7tBU1jJf8UKLzz72cqia4veEBzIfcPNGROCxg9fxSNy9ll6Tcw7&s=10", width=500)
    name = st.text_input("Enter Full Name")
    email = st.text_input("Enter Email")
    phone = st.text_input("Enter Phone Number")
    address = st.text_input("Enter Address")
    pwd = st.text_input("Choose a Password", type="password")
    btn = st.button("Register")

    if btn:
        db = get_db()
        result = db.execute_query(
            "INSERT INTO Members (name, email, phone, address, password) VALUES (%s, %s, %s, %s, %s)",
            (name, email, phone, address, pwd)
        )
        error = db.last_error

        if result:
            check = db.fetch_query("SELECT * FROM Members WHERE email = %s", (email,))
            st.subheader("Registration Successful")
            st.write(f"Connected to: host=`{db.host}`, database=`{db.database}`")
            st.write("Row now in the database:")
            st.dataframe(pd.DataFrame(check))
        else:
            st.error(f"Registration failed: {error}")

        db.disconnect()
