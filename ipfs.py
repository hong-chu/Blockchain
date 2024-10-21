import requests
import json

# Define headers with your Pinata API credentials
headers = {
    'pinata_api_key': '4dd854686002eb88d954',  # Replace with your actual API key
    'pinata_secret_api_key': 'ff88b043e1abcf32adcb15356821fd0fd20679aa6d4ebfde6f539681f02c9fbf',  # Replace with your actual secret API key
    'Content-Type': 'application/json'
}

# Function to pin data to IPFS using Pinata
def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary, but received {type(data)}"
    print(f"Attempting to pin data: {data}")
    try:
        # Make the request to Pinata to pin the data to IPFS
        response = requests.post("https://api.pinata.cloud/pinning/pinJSONToIPFS", headers=headers, json=data)
        response.raise_for_status()  # Raise an error for HTTP issues
        result = response.json()

        # Check if 'IpfsHash' is in the response
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

