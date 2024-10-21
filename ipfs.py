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

def get_from_ipfs(cid, content_type="json"):
    if cid is None:
        print("Error: CID is None. This might indicate a problem with pin_to_ipfs().")
        return None

    assert isinstance(cid, str), f"get_from_ipfs accepts a cid in the form of a string, but received {type(cid)}"
    
    try:
        response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
        response.raise_for_status()
        
        if content_type == "json":
            data = response.json()
        else:
            data = response.text
        
        print(f"Got from IPFS: {data}")
        
        if content_type == "json":
            assert isinstance(data, dict), f"get_from_ipfs should return a dict for JSON content type, but got {type(data)}"
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error making request to IPFS gateway: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response: {response.text if 'response' in locals() else 'No response'}")
    except AssertionError as e:
        print(f"Assertion error: {e}")
        print(f"Received data: {data if 'data' in locals() else 'No data'}")
    
    return None
