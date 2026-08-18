import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import settings

conn = sqlite3.connect(settings.db_path)
curr = conn.cursor()

curr.executescript("""
-- ============================================
-- DROP TABLES (in dependency order - children first)
-- ============================================
DROP TABLE IF EXISTS interactions;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

-- ============================================
-- CREATE TABLES (parent first)
-- ============================================

CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    phone           TEXT,
    city            TEXT,
    created_at      DATE DEFAULT CURRENT_DATE
);

CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    order_date      DATE NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    status          TEXT CHECK(status IN ('pending','shipped','delivered','cancelled')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE interactions (
    interaction_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL,
    channel         TEXT CHECK(channel IN ('email','chat','phone','social')),
    interaction_type TEXT,
    notes           TEXT,
    interaction_date DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================================
-- INSERT DATA: customers (10 rows)
-- ============================================
INSERT INTO customers (name, email, phone, city, created_at) VALUES
('Arjun Mehta', 'arjun.mehta@mail.com', '9876500001', 'Bengaluru', '2024-01-10'),
('Priya Nair', 'priya.nair@mail.com', '9876500002', 'Chennai', '2024-01-15'),
('Rohan Gupta', 'rohan.gupta@mail.com', '9876500003', 'Mumbai', '2024-02-01'),
('Sneha Iyer', 'sneha.iyer@mail.com', '9876500004', 'Hyderabad', '2024-02-10'),
('Vikram Rao', 'vikram.rao@mail.com', '9876500005', 'Pune', '2024-02-20'),
('Ananya Sharma', 'ananya.sharma@mail.com', '9876500006', 'Delhi', '2024-03-01'),
('Karthik Reddy', 'karthik.reddy@mail.com', '9876500007', 'Bengaluru', '2024-03-05'),
('Meera Pillai', 'meera.pillai@mail.com', '9876500008', 'Kochi', '2024-03-12'),
('Aditya Verma', 'aditya.verma@mail.com', '9876500009', 'Jaipur', '2024-03-20'),
('Divya Krishnan', 'divya.krishnan@mail.com', '9876500010', 'Chennai', '2024-04-01');

-- ============================================
-- INSERT DATA: orders (10 rows)
-- ============================================
INSERT INTO orders (customer_id, order_date, amount, status) VALUES
(1, '2024-04-01', 1250.00, 'delivered'),
(2, '2024-04-03', 899.50, 'shipped'),
(3, '2024-04-05', 430.75, 'pending'),
(4, '2024-04-07', 2100.00, 'delivered'),
(5, '2024-04-09', 675.25, 'cancelled'),
(6, '2024-04-11', 1500.00, 'delivered'),
(7, '2024-04-13', 320.00, 'shipped'),
(8, '2024-04-15', 980.40, 'pending'),
(9, '2024-04-17', 1750.60, 'delivered'),
(10, '2024-04-19', 560.00, 'shipped');

-- ============================================
-- INSERT DATA: interactions (10 rows)
-- ============================================
INSERT INTO interactions (customer_id, channel, interaction_type, notes, interaction_date) VALUES
(1, 'email', 'complaint', 'Delayed delivery inquiry', '2024-04-02'),
(2, 'chat', 'query', 'Asked about return policy', '2024-04-04'),
(3, 'phone', 'complaint', 'Order not received', '2024-04-06'),
(4, 'social', 'feedback', 'Positive review on Twitter', '2024-04-08'),
(5, 'email', 'cancellation', 'Requested order cancellation', '2024-04-10'),
(6, 'chat', 'query', 'Asked about payment options', '2024-04-12'),
(7, 'phone', 'query', 'Product availability check', '2024-04-14'),
(8, 'email', 'complaint', 'Wrong item shipped', '2024-04-16'),
(9, 'social', 'feedback', 'Shared unboxing video', '2024-04-18'),
(10, 'chat', 'query', 'Discount code not working', '2024-04-20');
""")

conn.commit()
conn.close()
print("[ok] DB added")