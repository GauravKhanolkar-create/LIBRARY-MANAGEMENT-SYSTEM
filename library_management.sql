DROP DATABASE IF EXISTS library_management;
CREATE DATABASE library_management;
USE library_management;

CREATE TABLE Category (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Staff (
    staff_id  INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(100) UNIQUE NOT NULL,
    role      VARCHAR(30) DEFAULT 'Librarian',
    password  VARCHAR(255) NOT NULL
);

CREATE TABLE Books (
    book_id           INT AUTO_INCREMENT PRIMARY KEY,
    title             VARCHAR(150) NOT NULL,
    author            VARCHAR(100) NOT NULL,
    category_id       INT,
    isbn              VARCHAR(20) UNIQUE,
    total_copies      INT NOT NULL DEFAULT 1,
    available_copies  INT NOT NULL DEFAULT 1,
    price             DECIMAL(8,2) DEFAULT 0.00,
    CONSTRAINT fk_book_category FOREIGN KEY (category_id)
        REFERENCES Category(category_id) ON DELETE SET NULL,
    CONSTRAINT chk_copies CHECK (available_copies >= 0 AND available_copies <= total_copies)
);

CREATE TABLE Members (
    member_id       INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    phone           VARCHAR(15),
    address         VARCHAR(200),
    password        VARCHAR(255) NOT NULL,
    membership_date DATE DEFAULT (CURRENT_DATE)
);

CREATE TABLE Transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id        INT NOT NULL,
    member_id      INT NOT NULL,
    staff_id       INT,
    issue_date     DATE NOT NULL,
    due_date       DATE NOT NULL,
    return_date    DATE NULL,
    status         ENUM('Issued','Returned') DEFAULT 'Issued',
    CONSTRAINT fk_txn_book   FOREIGN KEY (book_id)   REFERENCES Books(book_id),
    CONSTRAINT fk_txn_member FOREIGN KEY (member_id) REFERENCES Members(member_id),
    CONSTRAINT fk_txn_staff  FOREIGN KEY (staff_id)  REFERENCES Staff(staff_id)
);

CREATE TABLE Fine (
    fine_id        INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    amount         DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    paid_status    ENUM('Paid','Unpaid') DEFAULT 'Unpaid',
    CONSTRAINT fk_fine_txn FOREIGN KEY (transaction_id)
        REFERENCES Transactions(transaction_id)
);

ALTER TABLE Members ADD COLUMN status VARCHAR(20) DEFAULT 'Active';

INSERT INTO Category (category_name) VALUES
('Fiction'), ('Science'), ('History'), ('Technology');

INSERT INTO Staff (name, email, role, password) VALUES
('Anita Sharma', 'anita@library.com', 'Librarian', 'hashed_pw_1'),
('Rohan Mehta', 'rohan@library.com', 'Admin', 'hashed_pw_2');

INSERT INTO Books (title, author, category_id, isbn, total_copies, available_copies, price) VALUES
('The Alchemist', 'Paulo Coelho', 1, 'ISBN001', 5, 5, 299.00),
('A Brief History of Time', 'Stephen Hawking', 2, 'ISBN002', 3, 3, 450.00),
('Sapiens', 'Yuval Noah Harari', 3, 'ISBN003', 4, 4, 399.00),
('Clean Code', 'Robert C. Martin', 4, 'ISBN004', 2, 2, 550.00);

INSERT INTO Members (name, email, phone, address, password) VALUES
('Priya Singh', 'priya@example.com', '9876543210', 'Pune', 'priya123'),
('Aman Verma', 'aman@example.com', '9123456780', 'Mumbai', 'aman123');

UPDATE Members SET phone = '9999999999' WHERE member_id = 1;

SELECT * FROM Books;

SELECT b.title, b.author, c.category_name, b.available_copies
FROM Books b
JOIN Category c ON b.category_id = c.category_id;

SELECT c.category_name, COUNT(b.book_id) AS total_books
FROM Category c
LEFT JOIN Books b ON b.category_id = c.category_id
GROUP BY c.category_name;

SELECT name, email FROM Members
WHERE member_id IN (
    SELECT member_id FROM Transactions WHERE status = 'Issued'
);

SELECT t.transaction_id, m.name, b.title, t.due_date
FROM Transactions t
JOIN Members m ON t.member_id = m.member_id
JOIN Books b ON t.book_id = b.book_id
WHERE t.status = 'Issued' AND t.due_date < CURDATE();

CREATE USER IF NOT EXISTS 'librarian_user'@'localhost' IDENTIFIED BY 'Lib@1234';

GRANT SELECT, INSERT, UPDATE ON library_management.* TO 'librarian_user'@'localhost';

REVOKE UPDATE ON library_management.* FROM 'librarian_user'@'localhost';

FLUSH PRIVILEGES;

START TRANSACTION;

UPDATE Books SET available_copies = available_copies - 1 WHERE book_id = 1;
SAVEPOINT before_insert;

INSERT INTO Transactions (book_id, member_id, staff_id, issue_date, due_date)
VALUES (1, 1, 1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));

COMMIT;

DELIMITER //

CREATE PROCEDURE sp_IssueBook (
    IN p_book_id   INT,
    IN p_member_id INT,
    IN p_staff_id  INT,
    OUT p_message  VARCHAR(100)
)
BEGIN
    DECLARE v_available INT DEFAULT 0;

    SELECT available_copies INTO v_available
    FROM Books WHERE book_id = p_book_id;

    IF v_available IS NULL THEN
        SET p_message = 'Book not found';
    ELSEIF v_available <= 0 THEN
        SET p_message = 'No copies available';
    ELSE
        START TRANSACTION;

        INSERT INTO Transactions (book_id, member_id, staff_id, issue_date, due_date)
        VALUES (p_book_id, p_member_id, p_staff_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 14 DAY));

        UPDATE Books
        SET available_copies = available_copies - 1
        WHERE book_id = p_book_id;

        COMMIT;
        SET p_message = 'Book issued successfully';
    END IF;
END //

DELIMITER ;

DELIMITER //

CREATE FUNCTION fn_CalculateFine (p_transaction_id INT)
RETURNS DECIMAL(8,2)
DETERMINISTIC
BEGIN
    DECLARE v_due_date DATE;
    DECLARE v_return_date DATE;
    DECLARE v_overdue_days INT DEFAULT 0;
    DECLARE v_fine DECIMAL(8,2) DEFAULT 0.00;

    SELECT due_date, IFNULL(return_date, CURDATE())
    INTO v_due_date, v_return_date
    FROM Transactions
    WHERE transaction_id = p_transaction_id;

    IF v_return_date > v_due_date THEN
        SET v_overdue_days = DATEDIFF(v_return_date, v_due_date);
        SET v_fine = v_overdue_days * 5.00;
    END IF;

    RETURN v_fine;
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER trg_AfterReturn
AFTER UPDATE ON Transactions
FOR EACH ROW
BEGIN
    IF NEW.status = 'Returned' AND OLD.status = 'Issued' THEN

        UPDATE Books
        SET available_copies = available_copies + 1
        WHERE book_id = NEW.book_id;

        INSERT INTO Fine (transaction_id, amount, paid_status)
        VALUES (NEW.transaction_id, fn_CalculateFine(NEW.transaction_id), 'Unpaid');

    END IF;
END //

DELIMITER ;

