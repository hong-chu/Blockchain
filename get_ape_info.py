#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 16:32:15 2024

@author: hongchu
"""

from web3 import Web3
from web3.providers.rpc import HTTPProvider
import requests
import json


# Bored Ape contract address and ABI
bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# Load ABI from file
with open('/home/codio/workspace/abi.json', 'r') as f:
    abi = json.load(f)

# Connect to an Ethereum node (Infura or Alchemy URL)
api_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"  # Replace with your Ethereum node URL
provider = HTTPProvider(api_url)
web3 = Web3(provider)
assert web3.is_connected(), "Failed to connect to Ethereum node"

# Initialize contract instance
contract = web3.eth.contract(address=contract_address, abi=abi)

# Function to retrieve Bored Ape data
def get_ape_info(apeID):
    assert isinstance(apeID, int), f"{apeID} is not an int"
    assert 0 <= apeID <= 9999, f"{apeID} is out of the valid range"

    data = {'owner': "", 'image': "", 'eyes': ""}

    try:
        # Get the owner of the Bored Ape
        data['owner'] = contract.functions.ownerOf(apeID).call()

        # Get the token URI for metadata
        token_uri = contract.functions.tokenURI(apeID).call()

        # Convert IPFS URI format to HTTP URL for easier access
        ipfs_base_url = "https://ipfs.io/ipfs/"
        if token_uri.startswith("ipfs://"):
            token_uri = token_uri.replace("ipfs://", ipfs_base_url)

        # Fetch the metadata from IPFS
        metadata_response = requests.get(token_uri)
        metadata = metadata_response.json()

        # Extract image URL and eyes attribute
        data['image'] = metadata.get('image', "")

        # Locate 'eyes' attribute within metadata attributes
        attributes = metadata.get('attributes', [])
        eyes_attribute = next((attr['value'] for attr in attributes if attr['trait_type'] == 'Eyes'), "")
        data['eyes'] = eyes_attribute

    except Exception as e:
        print(f"Error fetching data for Ape ID {apeID}: {e}")

    # Validations to check the function’s output
    assert isinstance(data, dict), f'get_ape_info({apeID}) should return a dict'
    assert all(key in data for key in ['owner', 'image', 'eyes']), \
        "Return value should include the keys 'owner', 'image', and 'eyes'"

    return data
