import requests
import json


# Define headers with your Pinata API credentials
headers = {
    "Authorization": "Bearer 242eab8dfa2af3b47a64",
    "Content-Type": "application/json"
}

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE
	response = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS", headers=headers, data=json.dumps(data))
	cid = response.json()['IpfsHash']
	print(f"Pinned to IPFS: {cid}")

	return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	
	response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
	data = response.json()
	print(f"Got from IPFS: {data}")

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data
