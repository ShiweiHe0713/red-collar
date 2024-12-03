from faker import Faker
import random
import json

# Initialize Faker
fake = Faker()

# Define possible clothing items
clothing_items = [
    {'type': 'Jacket', 'sizes': ['XL'], 'colors': ['Red']},
    {'type': 'T-Shirt', 'sizes': ['S', 'M', 'L', 'XL'], 'colors': ['Red', 'Blue', 'Green', 'Black', 'White']},
    {'type': 'Jeans', 'sizes': ['28', '30', '32', '34', '36'], 'colors': ['Blue', 'Black', 'Gray']},
    {'type': 'Hoodie', 'sizes': ['S', 'M', 'L', 'XL'], 'colors': ['Black', 'Gray', 'White']},
    # Add more clothing items as needed
]

def generate_order():
    # in reallife the influxdb give the ts
    # we can manually write the ts
    order = {
        'order_id': fake.uuid4(),
        'customer': {
            'name': fake.name(),
            'email': fake.email(),
            'address': fake.address().replace('\n', ', '),
        },
        'items': [],
        'order_date': fake.date_this_year().isoformat(),
        'order_time': fake.time(),
        'status': random.choice(['Processing', 'Shipped', 'Delivered']),
    }
    
    # Randomly decide the number of items in the order
    num_items = random.randint(1, 5)
    
    for _ in range(num_items):
        item = random.choice(clothing_items)
        order['items'].append({
            'type': item['type'],
            'size': random.choice(item['sizes']),
            'color': random.choice(item['colors']),
            'quantity': random.randint(1, 3),
        })
    
    return order