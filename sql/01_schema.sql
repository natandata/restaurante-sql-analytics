CREATE TABLE restaurants(restaurant_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE products(product_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE menu(restaurant_id INTEGER REFERENCES restaurants,product_id INTEGER REFERENCES products,price_cents INTEGER NOT NULL CHECK(price_cents>0),cost_cents INTEGER NOT NULL CHECK(cost_cents>=0),PRIMARY KEY(restaurant_id,product_id));
CREATE TABLE orders(order_id INTEGER PRIMARY KEY,restaurant_id INTEGER NOT NULL REFERENCES restaurants,ordered_at TEXT NOT NULL,total_cents INTEGER NOT NULL CHECK(total_cents>=0),UNIQUE(order_id,restaurant_id));
CREATE TABLE order_lines(order_id INTEGER NOT NULL,product_id INTEGER NOT NULL,restaurant_id INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),unit_cents INTEGER NOT NULL CHECK(unit_cents>0),PRIMARY KEY(order_id,product_id),FOREIGN KEY(order_id,restaurant_id) REFERENCES orders(order_id,restaurant_id),FOREIGN KEY(restaurant_id,product_id) REFERENCES menu(restaurant_id,product_id));
CREATE INDEX ix_orders_date ON orders(ordered_at);
CREATE VIEW order_totals AS SELECT order_id,SUM(quantity*unit_cents) AS line_total_cents FROM order_lines GROUP BY order_id;
