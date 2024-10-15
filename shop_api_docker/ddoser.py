from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from faker import Faker

faker = Faker()


def create_item():
    for _ in range(500):
        response = requests.post("http://localhost:8000/cart/")
        print(response)


with ThreadPoolExecutor() as executor:
    futures = {}

    for i in range(15):
        futures[executor.submit(create_item)] = f"item-{i}"

    for future in as_completed(futures):
        print(f"completed {futures[future]}")
