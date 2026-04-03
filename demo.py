import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def show(response):
    data = response.json()
    print(json.dumps(data, indent=2))

print_section("ShopSphere - Live Demo")

# 1. Health Check
print_section("1. System Health Check")
show(requests.get(f"{BASE_URL}/api/health"))

# 2. Search Products
print_section("2. Search: 'apple' (ElasticSearch Simulated)")
show(requests.get(f"{BASE_URL}/api/search?q=apple&sort_by=price_asc"))

# 3. Add to Cart
print_section("3. Add to Cart (Redis Simulated)")
show(requests.post(f"{BASE_URL}/api/cart/U001/add", json={"product_id": "P003", "quantity": 1}))
show(requests.post(f"{BASE_URL}/api/cart/U001/add", json={"product_id": "P008", "quantity": 2}))

# 4. View Cart
print_section("4. View Cart")
show(requests.get(f"{BASE_URL}/api/cart/U001"))

# 5. Checkout
print_section("5. Checkout (Stripe Payment Simulated)")
show(requests.post(f"{BASE_URL}/api/orders/U001/checkout", json={"payment_method": "card"}))

# 6. Order History
print_section("6. Order History")
show(requests.get(f"{BASE_URL}/api/orders/U001/history"))

# 7. Recommendations
print_section("7. AI Recommendations (Collaborative Filtering)")
show(requests.get(f"{BASE_URL}/api/recommendations/U001"))

# 8. Event Log
print_section("8. Message Broker Event Log (RabbitMQ Simulated)")
show(requests.get(f"{BASE_URL}/api/events"))

print_section("Demo Complete!")
print("All 4 microservices working:")
print("  Service A - Auth/User: Users & Sessions")
print("  Service B - Product/Search: ElasticSearch Simulation")
print("  Service C - Orders: Stripe + Event-Driven (RabbitMQ)")
print("  Service D - Recommendations: Collaborative Filtering AI")
