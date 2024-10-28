from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
import requests
import json
import time

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

#You will need the ABI to connect to the contract
#The file 'abi.json' has the ABI for the bored ape contract
#In general, you can get contract ABIs from etherscan
#https://api.etherscan.io/api?module=contract&action=getabi&address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D
with open('abi.json', 'r') as f:
	abi = json.load(f) 

############################
#Connect to an Ethereum node
api_url = "https://mainnet.infura.io/v3/784304505f3148789fea389712f68321"
provider = HTTPProvider(api_url)
web3 = Web3(provider)

assert web3.is_connected(), "Failed to connect to Ethereum node"

# Initialize contract instance
contract = web3.eth.contract(address=contract_address, abi=abi)

def get_ape_info(apeID):
    assert isinstance(apeID,int), f"{apeID} is not an int"
    assert 1 <= apeID, f"{apeID} must be at least 1"

    data = {'owner': "", 'image': "", 'eyes': "" }
	
	#YOUR CODE HERE	
    try:
        # Get the owner of the Bored Ape
        data['owner'] = contract.functions.ownerOf(apeID).call()

        # Get the token URI for metadata
        token_uri = contract.functions.tokenURI(apeID).call()

        # Fetch the metadata from the token URI
        metadata_response = requests.get(token_uri)
        metadata = metadata_response.json()

        # Extract image URL and eye attribute
        data['image'] = metadata.get('image', "")
        
        # Locate 'eyes' attribute in metadata attributes
        attributes = metadata.get('attributes', [])
        eyes_attribute = next((attr['value'] for attr in attributes if attr['trait_type'] == 'Eyes'), "")
        data['eyes'] = eyes_attribute

    except Exception as e:
        print(f"Error fetching data for Ape ID {apeID}: {e}")


    assert isinstance(data,dict), f'get_ape_info{apeID} should return a dict' 
    assert all( [a in data.keys() for a in ['owner','image','eyes']] ), f"return value should include the keys 'owner','image' and 'eyes'"
    return data

