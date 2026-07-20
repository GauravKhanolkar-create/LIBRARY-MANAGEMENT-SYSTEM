import mysql.connector
from mysql.connector import Error


class connectDB:
    def __init__(self, host="localhost", user="root", password="", database="library_management"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.dict_cursor = None
        self.last_error = None

    def connect(self):
        """Open a connection to the MySQL server/database."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()              
                self.dict_cursor = self.connection.cursor(dictionary=True)  
                print(f"Connected to database '{self.database}' successfully.")
            return True
        except Error as e:
            self.last_error = str(e)
            print(f"Error while connecting to MySQL: {e}")
            return False

    def disconnect(self):
        """Close the cursors and connection."""
        if self.cursor:
            self.cursor.close()
        if self.dict_cursor:
            self.dict_cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")

    def execute_query(self, query, params=None):
        """
        Execute a query that does not return rows
        (CREATE, INSERT, UPDATE, DELETE, GRANT, REVOKE, etc.)
        Commits automatically. Returns number of affected rows.
        """
        if not self.connection or not self.connection.is_connected():
            self.last_error = "Not connected to the database."
            print("Cannot execute query: not connected to the database.")
            return None
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor.rowcount
        except Error as e:
            self.last_error = str(e)
            print(f"Error executing query: {e}")
            self.connection.rollback()
            return None

    def fetch_query(self, query, params=None):
        """Execute a SELECT query and return all rows as a list of dicts."""
        if not self.connection or not self.connection.is_connected():
            self.last_error = "Not connected to the database."
            print("Cannot fetch query: not connected to the database.")
            return None
        try:
            self.dict_cursor.execute(query, params or ())
            return self.dict_cursor.fetchall()
        except Error as e:
            self.last_error = str(e)
            print(f"Error fetching query: {e}")
            return None

    def start_transaction(self):
        self.connection.start_transaction()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def call_procedure(self, proc_name, args=()):
        """
        Call a stored procedure. For procedures with OUT params,
        pass placeholder values in `args` for OUT params (e.g. 0 or '').
        Returns the resolved OUT/INOUT parameter values.
        """
        if not self.connection or not self.connection.is_connected():
            self.last_error = "Not connected to the database."
            return None
        try:
            result_args = self.cursor.callproc(proc_name, args)
            self.connection.commit()
            return result_args
        except Error as e:
            self.last_error = str(e)
            print(f"Error calling procedure {proc_name}: {e}")
            self.connection.rollback()
            return None

    def call_function(self, func_name, args=()):
        """Call a stored FUNCTION using a SELECT statement."""
        placeholders = ", ".join(["%s"] * len(args))
        query = f"SELECT {func_name}({placeholders}) AS result"
        row = self.fetch_query(query, args)
        return row[0]["result"] if row else None

if __name__ == "__main__":
    db = connectDB(host="localhost", user="root", password="your_password")

    if db.connect():
        books = db.fetch_query("SELECT * FROM Books")
        print("Books:", books)

        rows = db.execute_query(
            "INSERT INTO Members (name, email, phone, address, password) VALUES (%s, %s, %s, %s, %s)",
            ("Sneha Kulkarni", "sneha@example.com", "9812345678", "Nagpur", "sneha123")
        )
        print("Insert result:", rows, "| error:", db.last_error)

        result = db.call_procedure("sp_IssueBook", (1, 1, 1, ""))
        print("Procedure result (OUT message):", result[3] if result else db.last_error)

        fine = db.call_function("fn_CalculateFine", (1,))
        print("Calculated fine:", fine)

        db.start_transaction()
        db.execute_query("UPDATE Books SET price = price + 10 WHERE book_id = 1")
        db.commit()  

        db.disconnect()
