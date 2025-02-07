import requests
import json

url = "https://blue.triple-lab.com/raid/74"
resp = requests.get(url)
data = json.loads(resp.text)

b = data["b"]

ranks_to_get = [1, 1000, 2500, 5000, 7000,10000, 15000, 20000]
results = {rank: b.get(str(rank), None) for rank in ranks_to_get}
print(results)
