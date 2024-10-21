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
	with open(contract_json, "r") as f:
		d = json.load(f)
		d = d['bsc']
		address = d['address']
		abi = d['abi']

	# connect to BNB url
	url = "https://bsc-dataseed1.binance.org/"
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"

        print(f"Connected to BNB testnet: {w3.is_connected()}")
        if w3.is_connected():
            print(f"Chain ID: {w3.eth.chain_id}")
        else:
            print("Failed to connect to the BNB testnet")
	
	# inject middleware
	w3.middleware_stack.inject(geth_poa_middleware, layer=0)
	
	# connect to a contract called “MerkleValidator”
	contract = w3.eth.contract(address=address, abi=abi)

	return w3, contract
