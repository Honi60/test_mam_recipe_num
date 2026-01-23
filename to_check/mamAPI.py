import requests

url = "https://api.misim.gov.il/invoice-allocation"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "supplier_id": "123456789",
    "client_id": "987654321",
    "invoice_amount": 25000,
    "invoice_date": "2025-07-12"
}

response = requests.post(url, json=data, headers=headers)
allocation_number = response.json().get("allocation_number")
print("מספר הקצאה:", allocation_number)