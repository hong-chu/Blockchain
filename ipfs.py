import requests
import json

# Define headers with your Pinata API credentials
headers = {
    'pinata_api_key': '0b7b7645f5d556faef30',  # Replace with your actual API key
    'pinata_secret_api_key': '2945a247c3621017722fc1cdc6fbb1c8e52cb4d5c649987fb3ae0d2b67084c2b',  # Replace with your actual secret API key
    'Content-Type': 'application/json'
}

# Function to pin data to IPFS using Pinata
def pin_to_ipfs(data):
    assert isinstance(data, dict), f"Error pin_to_ipfs expects a dictionary"
    
    try:
        # Pin JSON data to IPFS using Pinata
        response = requests.post(
            "https://api.pinata.cloud/pinning/pinJSONToIPFS",
            headers=headers,
            json=data  # Convert the dictionary to JSON
        )
        response.raise_for_status()  # Raise an error for HTTP issues
        result = response.json()

        # Extract and return the CID from the response
        if 'IpfsHash' not in result:
            raise KeyError("'IpfsHash' not found in the response")
        cid = result['IpfsHash']
        print(f"Successfully pinned to IPFS. CID: {cid}")
        return cid
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Pinata: {e}")
        return None

# Function to retrieve data from IPFS using a CID
def get_from_ipfs(cid, content_type="json"):
    assert isinstance(cid, str), f"get_from_ipfs accepts a cid in the form of a string"
    
    try:
        # Retrieve data from IPFS using the CID
        response = requests.get(f"https://gateway.pinata.cloud/ipfs/{cid}")
        response.raise_for_status()  # Raise an error for HTTP issues

        # Assuming JSON content, return the data as a dictionary
        data = response.json()
        print(f"Successfully retrieved data from IPFS: {data}")
        
        # Ensure the returned data is a dictionary
        assert isinstance(data, dict), f"get_from_ipfs should return a dict, but returned {type(data)}"
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving from IPFS: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response: {response.text if 'response' in locals() else 'No response'}")
    
    return None


# Example dictionary to pin to IPFS
data_to_pin = {
    "name": "Bored Ape",
    "description": "A test ape from the collection",
    "attributes": [
        {"trait_type": "Fur", "value": "Noise"},
        {"trait_type": "Eyes", "value": "Bored"}
    ]
}

# Pin data to IPFS
cid = pin_to_ipfs(data_to_pin)

# Retrieve data from IPFS using the CID
if cid:
    data_from_ipfs = get_from_ipfs(cid)
    print(f"Data from IPFS: {data_from_ipfs}")
