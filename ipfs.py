import requests
import json


# Define headers with your Pinata API credentials
headers = {
    "Authorization": "Bearer 242eab8dfa2af3b47a64",
    "Content-Type": "application/json"
}

# def pin_to_ipfs(data):
# 	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
# 	#YOUR CODE HERE
# 	response = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS", headers=headers, data=json.dumps(data))
# 	cid = response.json()['IpfsHash']
# 	print(f"Pinned to IPFS: {cid}")

# 	return cid


def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"
    try:
        response = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS", headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raises an HTTPError for bad responses
        result = response.json()
        if 'IpfsHash' not in result:
            raise KeyError("'IpfsHash' not found in the response")
        cid = result['IpfsHash']
        print(f"Pinned to IPFS: {cid}")
        return cid
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Pinata: {e}")
        print(f"Response content: {response.text}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response: {response.text}")
    except KeyError as e:
        print(f"Error accessing response data: {e}")
        print(f"Full response: {result}")
    return None

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	
	response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
	data = response.json()
	print(f"Got from IPFS: {data}")

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data
