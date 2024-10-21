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
    print(cid)
    if cid is None:
        print("Error: CID is None. This might indicate a problem with pin_to_ipfs().")
        return None

    if not isinstance(cid, str):
        print(f"Error: CID must be a string, but received {type(cid)}")
        return None

    try:
        print(f"Attempting to retrieve data for CID: {cid}")
        response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
        response.raise_for_status()  # Raise an error for HTTP issues

        # Handle different content types
        if content_type == "json":
            try:
                data = response.json()  # Try to parse as JSON
                print(f"Successfully retrieved JSON data from IPFS: {data}")
                if not isinstance(data, dict):
                    print(f"Warning: Retrieved data is not a dictionary. Type: {type(data)}")
                return data
            except json.JSONDecodeError:
                print(f"Error: Failed to decode JSON from the response. Response content: {response.text}")
                return None
        else:
            # For non-JSON content types (e.g., text, binary)
            data = response.content  # Get the raw content
            print(f"Successfully retrieved raw data from IPFS. Content type: {content_type}")
            return data

    except requests.exceptions.RequestException as e:
        print(f"Error making request to IPFS gateway: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None
