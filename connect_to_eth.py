# -*- coding: utf-8 -*-

import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider

'''If you use one of the suggested infrastructure providers, the url will be of the form
now_url  = f"https://eth.nownodes.io/{now_token}"
alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
infura_url = f"https://mainnet.infura.io/v3/{infura_token}"
'''


def connect_to_eth():
	url = "https://mainnet.infura.io/v3/784304505f3148789fea389712f68321"  # FILL THIS IN
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	return w3


def connect_with_middleware(contract_json):
def connect_with_middleware(contract_json):
    with open(contract_json, "r") as f:
        d = json.load(f)
        d = d['bsc']
        address = d['address']
        abi = d['abi']
    
    print(f"Contract address: {address}")
    print(f"ABI length: {len(abi)}")

    # connect to BNB testnet url
    url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BNB testnet URL
    w3 = Web3(Web3.HTTPProvider(url))
    
    print(f"Connected to BNB testnet: {w3.is_connected()}")
    if w3.is_connected():
        print(f"Chain ID: {w3.eth.chain_id}")
    else:
        print("Failed to connect to the BNB testnet")
        return None, None

    # inject middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    # connect to the MerkleValidator contract
    contract = w3.eth.contract(address=address, abi=abi)

    # Try to call a simple view function
    # Replace 'someFunction' with an actual function name from your MerkleValidator contract
    try:
        # Example: result = contract.functions.isValidProof(...).call()
        # You need to replace this with a real function call from your contract
        print("Available functions:", [func for func in contract.functions])
        # result = contract.functions.someFunction().call()
        # print(f"Successfully called contract function. Result: {result}")
    except Exception as e:
        print(f"Error calling contract function: {str(e)}")

    return w3, contract

# Test the function
w3, contract = connect_with_middleware('path/to/your/contract_info.json')
if w3 and contract:
    print("Successfully connected and created contract instance")
else:
    print("Failed to connect or create contract instance")
	
if __name__ == "__main__":
	connect_to_eth()
