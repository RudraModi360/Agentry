-- Product table creation and sample data
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT
);

-- Insert 3 sample products
INSERT INTO products (name, price, description) VALUES
    ('Red T‑Shirt', 19.99, 'A comfortable red cotton t‑shirt.'),
    ('Blue Jeans', 49.99, 'Stylish blue denim jeans.'),
    ('Wireless Mouse', 25.50, 'Ergonomic wireless mouse with adjustable DPI.');
