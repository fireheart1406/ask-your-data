import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "questions.json")
NEW_QUESTIONS = [
    {"id": 41, "level": "unseen", "question": "total revenue from orders paid by UPI?",
     "gold_sql": "SELECT SUM(oi.quantity * oi.unit_price) FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.status <> 'cancelled' AND o.payment_method = 'UPI'"},
    {"id": 42, "level": "unseen", "question": "How many customers placed exactly one order?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*) = 1) t"},
    {"id": 43, "level": "unseen", "question": "What is the average number of different products per order, rounded to 2 decimals?",
     "gold_sql": "SELECT ROUND(AVG(n), 2) FROM (SELECT order_id, COUNT(DISTINCT product_id) AS n FROM order_items GROUP BY order_id) t"},
    {"id": 44, "level": "unseen", "question": "How many orders were placed by customers from the city of Delhi in 2026?",
     "gold_sql": "SELECT COUNT(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE c.city = 'Delhi' AND EXTRACT(YEAR FROM o.order_date) = 2026"},
    {"id": 45, "level": "unseen", "question": "List the 3 cheapest products in each category. Show category and product name.",
     "gold_sql": "SELECT category, product_name FROM (SELECT category, product_name, ROW_NUMBER() OVER (PARTITION BY category ORDER BY unit_price) AS rn FROM products) t WHERE rn <= 3"},
    {"id": 46, "level": "unseen", "question": "Ignoring the year, which month number has the most orders placed? Show the month number and the count.",
     "gold_sql": "SELECT EXTRACT(MONTH FROM order_date) AS month, COUNT(*) AS n FROM orders GROUP BY 1 ORDER BY n DESC LIMIT 1"},
    {"id": 47, "level": "unseen", "question": "How many customers have ordered products from at least 3 different categories?",
     "gold_sql": "SELECT COUNT(*) FROM (SELECT o.customer_id FROM orders o JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id GROUP BY o.customer_id HAVING COUNT(DISTINCT p.category) >= 3) t"},
    {"id": 48, "level": "unseen", "question": "whats the biggest single order by value? just the order id and its total",
     "gold_sql": "SELECT o.order_id, SUM(oi.quantity * oi.unit_price) AS total FROM orders o JOIN order_items oi ON oi.order_id = o.order_id WHERE o.status <> 'cancelled' GROUP BY o.order_id ORDER BY total DESC LIMIT 1"},
    {"id": 49, "level": "unseen", "question": "Compare 2025 and 2026: how many orders were placed in each year? Show year and count.",
     "gold_sql": "SELECT EXTRACT(YEAR FROM order_date) AS year, COUNT(*) FROM orders WHERE EXTRACT(YEAR FROM order_date) IN (2025, 2026) GROUP BY 1"},
    {"id": 50, "level": "unseen", "question": "Among customers who signed up in 2025, what percentage placed at least one order? Round to 2 decimals.",
     "gold_sql": "SELECT ROUND(100.0 * COUNT(DISTINCT o.customer_id) / COUNT(DISTINCT c.customer_id), 2) FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id WHERE EXTRACT(YEAR FROM c.signup_date) = 2025"},
]
with open(PATH, encoding="utf-8") as f:
    questions = json.load(f)
existing_ids = {q["id"] for q in questions}
added = 0
for q in NEW_QUESTIONS:
    if q["id"] not in existing_ids:
        questions.append(q)
        added += 1
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(questions, f, indent=2)
print(f"Added {added} questions. Total now: {len(questions)}")