import requests

url = "http://127.0.0.1:5000/panos_detect_and_classify"
payload = {
    "lat": 12.809739,
    "lon": 80.087353,
    "count": 3,
    "area_of_interest": 4000,
    "min_distance": 20,
    "labels": ["tree", "bushes"]  # Optional: specify object labels
}

response = requests.post(url, json=payload)
print("Panoramic Detect & Classify API response:")
print(response.json())

# 12.809739, 80.087353

