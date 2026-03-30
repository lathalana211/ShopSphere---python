from flask import Flask, request, jsonify, session, render_template, send_from_directory
from flask_cors import CORS
import uuid
import math
from datetime import datetime
import threading
import queue
import random

app = Flask(__name__, template_folder='templates')
app.secret_key = "shopsphere-secret-2024"
CORS(app)  # Allow frontend to talk to API
===========================================================

PRODUCTS = {
    "P001": {"id": "P001", "name": "iPhone 15 Pro", "category": "Electronics", "price": 999.99, "stock": 50, "vendor": "V001", "tags": ["phone", "apple", "mobile"]},
    "P002": {"id": "P002", "name": "Samsung Galaxy S24", "category": "Electronics", "price": 849.99, "stock": 35, "vendor": "V002", "tags": ["phone", "samsung", "android"]},
    "P003": {"id": "P003", "name": "MacBook Air M3", "category": "Laptops", "price": 1299.99, "stock": 20, "vendor": "V001", "tags": ["laptop", "apple", "mac"]},
    "P004": {"id": "P004", "name": "Dell XPS 15", "category": "Laptops", "price": 1199.99, "stock": 15, "vendor": "V003", "tags": ["laptop", "dell", "windows"]},
    "P005": {"id": "P005", "name": "Sony WH-1000XM5", "category": "Audio", "price": 349.99, "stock": 60, "vendor": "V002", "tags": ["headphones", "sony", "wireless"]},
    "P006": {"id": "P006", "name": "AirPods Pro 2", "category": "Audio", "price": 249.99, "stock": 80, "vendor": "V001", "tags": ["earbuds", "apple", "wireless"]},
    "P007": {"id": "P007", "name": "iPad Pro 12.9", "category": "Tablets", "price": 1099.99, "stock": 25, "vendor": "V001", "tags": ["tablet", "apple", "ipad"]},
    "P008": {"id": "P008", "name": "Logitech MX Master 3", "category": "Accessories", "price": 99.99, "stock": 120, "vendor": "V004", "tags": ["mouse", "logitech", "wireless"]},
    "P009": {"id": "P009", "name": "Samsung 4K Monitor", "category": "Monitors", "price": 599.99, "stock": 30, "vendor": "V002", "tags": ["monitor", "samsung", "4k"]},
    "P010": {"id": "P010", "name": "Mechanical Keyboard", "category": "Accessories", "price": 129.99, "stock": 90, "vendor": "V004", "tags": ["keyboard", "mechanical", "gaming"]},
}

VENDORS = {
    "V001": {"id": "V001", "name": "Apple Store", "rating": 4.8},
    "V002": {"id": "V002", "name": "Samsung Hub", "rating": 4.5},
    "V003": {"id": "V003", "name": "Dell Official", "rating": 4.3},
    "V004": {"id": "V004", "name": "Logitech World", "rating": 4.6},
}

USERS = {
    "U001": {"id": "U001", "name": "Alice", "email": "alice@email.com", "purchase_history": ["P001", "P006", "P007"]},
    "U002": {"id": "U002", "name": "Bob", "email": "bob@email.com", "purchase_history": ["P003", "P008", "P010"]},
    "U003": {"id": "U003", "name": "Charlie", "email": "charlie@email.com", "purchase_history": ["P002", "P005", "P009"]},
    "U004": {"id": "U004", "name": "Diana", "email": "diana@email.com", "purchase_history": ["P001", "P003", "P008"]},
}

ORDERS = {}
CARTS = {}

event_queue = queue.Queue()
event_log = []

def event_worker():
    """Background worker simulating RabbitMQ message consumer"""
    while True:
        try:
            event = event_queue.get(timeout=1)
            process_event(event)
            event_queue.task_done()
        except queue.Empty:
            continue

def process_event(event):
    """Handle events: inventory update, vendor notify, cache invalidate"""
    event_log.append({
        "timestamp": datetime.now().isoformat(),
        "type": event["type"],
        "data": event["data"]
    })
    if event["type"] == "ORDER_PLACED":
        product_id = event["data"]["product_id"]
        qty = event["data"]["quantity"]
        if product_id in PRODUCTS:
            PRODUCTS[product_id]["stock"] -= qty
    elif event["type"] == "RESTOCK":
        product_id = event["data"]["product_id"]
        qty = event["data"]["quantity"]
        if product_id in PRODUCTS:
            PRODUCTS[product_id]["stock"] += qty

def publish_event(event_type, data):
    event_queue.put({"type": event_type, "data": data})

# Start background worker thread
worker_thread = threading.Thread(target=event_worker, daemon=True)
worker_thread.start()


def search_products(query, category=None, min_price=None, max_price=None, sort_by="relevance"):
    """Simulates ElasticSearch fuzzy full-text search"""
    query_lower = query.lower() if query else ""
    results = []

    for product in PRODUCTS.values():
        score = 0

        # Fuzzy name match
        if query_lower in product["name"].lower():
            score += 10
        # Tag match
        for tag in product["tags"]:
            if query_lower in tag:
                score += 5
        # Category match
        if query_lower in product["category"].lower():
            score += 3

        if score == 0 and query_lower:
            continue

        # Filters
        if category and product["category"] != category:
            continue
        if min_price and product["price"] < float(min_price):
            continue
        if max_price and product["price"] > float(max_price):
            continue

        results.append({**product, "_score": score})

    # Sort
    if sort_by == "price_asc":
        results.sort(key=lambda x: x["price"])
    elif sort_by == "price_desc":
        results.sort(key=lambda x: x["price"], reverse=True)
    else:
        results.sort(key=lambda x: x["_score"], reverse=True)

    return results


def build_user_item_matrix():
    """Build user-product interaction matrix"""
    matrix = {}
    for user_id, user in USERS.items():
        matrix[user_id] = set(user["purchase_history"])
    return matrix

def cosine_similarity(set_a, set_b):
    """Calculate similarity between two users based on shared products"""
    if not set_a or not set_b:
        return 0
    intersection = len(set_a & set_b)
    return intersection / math.sqrt(len(set_a) * len(set_b))

def get_recommendations(user_id, top_n=4):
    """Collaborative filtering: 'Users who bought X also bought Y'"""
    if user_id not in USERS:
        return []

    matrix = build_user_item_matrix()
    current_user_products = matrix[user_id]

    # Find similar users
    similarities = []
    for other_id, other_products in matrix.items():
        if other_id == user_id:
            continue
        sim = cosine_similarity(current_user_products, other_products)
        if sim > 0:
            similarities.append((other_id, sim, other_products))

    similarities.sort(key=lambda x: x[1], reverse=True)

    # Collect products from similar users that current user hasn't bought
    recommended = {}
    for other_id, sim, other_products in similarities:
        new_products = other_products - current_user_products
        for pid in new_products:
            if pid not in recommended:
                recommended[pid] = 0
            recommended[pid] += sim

    # Sort by score
    sorted_recs = sorted(recommended.items(), key=lambda x: x[1], reverse=True)
    result = []
    for pid, score in sorted_recs[:top_n]:
        if pid in PRODUCTS:
            result.append({**PRODUCTS[pid], "recommendation_score": round(score, 2)})

    return result


@app.route("/api/products", methods=["GET"])
def get_all_products():
    return jsonify({"success": True, "products": list(PRODUCTS.values()), "total": len(PRODUCTS)})

@app.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    product = PRODUCTS.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404
    vendor = VENDORS.get(product["vendor"], {})
    return jsonify({"success": True, "product": product, "vendor": vendor})

@app.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    category = request.args.get("category")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    sort_by = request.args.get("sort_by", "relevance")

    results = search_products(query, category, min_price, max_price, sort_by)
    return jsonify({
        "success": True,
        "query": query,
        "results": results,
        "total": len(results),
        "latency_ms": random.randint(12, 48)  # Simulated <100ms ElasticSearch latency
    })

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "app": "ShopSphere API",
        "version": "1.0.0",
        "brand": "ShopSphere - Scalable Marketplace",
        "endpoints": {
            "GET  /api/products": "List all products",
            "GET  /api/products/<id>": "Get product detail",
            "GET  /api/search?q=<query>": "Search products (ElasticSearch simulated)",
            
        }
    })

if __name__ == "__main__":
    print("=" * 60)
    print("  ShopSphere - Scalable Marketplace API")
    print("  Running on http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000) 
