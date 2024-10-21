import requests
import json


# Define headers with your Pinata API credentials
headers = {
    "Authorization": "Bearer 242eab8dfa2af3b47a64",
    "Content-Type": "application/json"
}

def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary, but received {type(data)}"
    print(f"Attempting to pin data: {data}")
    try:
        response = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"Pinata API response: {result}")
        if 'IpfsHash' not in result:
            raise KeyError("'IpfsHash' not found in the response")
        cid = result['IpfsHash']
        print(f"Successfully pinned to IPFS. CID: {cid}")
        return cid
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Pinata: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response: {response.text if 'response' in locals() else 'No response'}")
    except KeyError as e:
        print(f"Error accessing response data: {e}")
        print(f"Full response: {result if 'result' in locals() else 'No result'}")
    
    print("Failed to pin data to IPFS. Returning None.")
    return None


def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), f"get_from_ipfs accepts a cid in the form of a string"
    try:
        response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        if content_type == "json":
            data = response.json()
        else:
            data = response.text
        
        print(f"Got from IPFS: {data}")
        
        if content_type == "json":
            assert isinstance(data, dict), f"get_from_ipfs should return a dict for JSON content type"
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error making request to IPFS gateway: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response: {response.text}")
    except AssertionError as e:
        print(f"Assertion error: {e}")
    
    return None  # Return None only if an exception occurred