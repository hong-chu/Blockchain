#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 15:25:34 2024

@author: hongchu
"""

# -*- coding: utf-8 -*-

import random
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.providers.rpc import HTTPProvider


# If you use one of the suggested infrastructure providers, the url will be of the form
# now_url  = f"https://eth.nownodes.io/{now_token}"
# alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
# infura_url = f"https://mainnet.infura.io/v3/{infura_token}"

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

	# TODO complete this method
	# The first section will be the same as "connect_to_eth()" but with a BNB url
    bnb_url = "https://bsc-testnet.blockpi.network/v1/rpc/public"
    w3 = Web3(HTTPProvider(bnb_url))

    # Inject middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    assert w3.is_connected(), f"Failed to connect to BNB provider at {bnb_url}"

	# The second section requires you to inject middleware into your w3 object and
	# create a contract object. Read more on the docs pages at https://web3py.readthedocs.io/en/stable/middleware.html
	# and https://web3py.readthedocs.io/en/stable/web3.contract.html
    contract = w3.eth.contract(address=address, abi=abi)

    return w3, contract



def is_ordered_block(w3, block_num):
    """
	Takes a block number
	Returns a boolean that tells whether all the transactions in the block are ordered by priority fee

	Before EIP-1559, a block is ordered if and only if all transactions are sorted in decreasing order of the gasPrice field

	After EIP-1559, there are two types of transactions
		*Type 0* The priority fee is tx.gasPrice - block.baseFeePerGas
		*Type 2* The priority fee is min( tx.maxPriorityFeePerGas, tx.maxFeePerGas - block.baseFeePerGas )

	Conveniently, most type 2 transactions set the gasPrice field to be min( tx.maxPriorityFeePerGas + block.baseFeePerGas, tx.maxFeePerGas )
	"""
    block = w3.eth.get_block(block_num, full_transactions=True)
    ordered = True  # Start with the assumption that the block is ordered
    
    # Fetch base fee per gas if available (only present in EIP-1559 blocks)
    base_fee = block.get('baseFeePerGas', None)

    # Initialize variable to store the priority fee of the previous transaction
    previous_priority_fee = None

    # Iterate over all transactions in the block
    for tx in block.transactions:
        # Determine priority fee based on transaction type
        if 'maxPriorityFeePerGas' in tx and 'maxFeePerGas' in tx and base_fee is not None:
            # Type 2 transaction with EIP-1559
            priority_fee = min(tx['maxPriorityFeePerGas'], tx['maxFeePerGas'] - base_fee)
        elif base_fee is not None:
            # Type 0 transaction in a post-EIP-1559 block with base fee
            priority_fee = tx.gasPrice - base_fee
        else:
            # Pre-EIP-1559 or Type 0 transaction without base fee
            priority_fee = tx.gasPrice

        # Check if the transactions are in decreasing order by priority fee
        if previous_priority_fee is not None and priority_fee > previous_priority_fee:
            ordered = False  # Found unordered transaction
            break  # No need to continue if we find an unordered transaction

        # Update the previous priority fee for the next comparison
        previous_priority_fee = priority_fee

    return ordered


def get_contract_values(contract, admin_address, owner_address):
    """
	Takes a contract object, and two addresses (as strings) to be used for calling
	the contract to check current on chain values.
	The provided "default_admin_role" is the correctly formatted solidity default
	admin value to use when checking with the contract
	To complete this method you need to make three calls to the contract to get:
	  onchain_root: Get and return the merkleRoot from the provided contract
	  has_role: Verify that the address "admin_address" has the role "default_admin_role" return True/False
	  prime: Call the contract to get and return the prime owned by "owner_address"

	check on available contract functions and transactions on the block explorer at
	https://testnet.bscscan.com/address/0xaA7CAaDA823300D18D3c43f65569a47e78220073
	"""
    default_admin_role = int.to_bytes(0, 32, byteorder="big")

    # TODO complete the following lines by performing contract calls
    # Call contract functions
    onchain_root = contract.functions.merkleRoot().call()
    has_role = contract.functions.hasRole(default_admin_role, admin_address).call()
    prime = contract.functions.getPrimeByOwner(owner_address).call()

    return onchain_root, has_role, prime



"""
	This might be useful for testing (main is not run by the grader feel free to change 
	this code anyway that is helpful)
"""
if __name__ == "__main__":
	# These are addresses associated with the Merkle contract (check on contract
	# functions and transactions on the block explorer at
	# https://testnet.bscscan.com/address/0xaA7CAaDA823300D18D3c43f65569a47e78220073
	admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
	owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
	contract_file = "contract_info.json"

	eth_w3 = connect_to_eth()
	cont_w3, contract = connect_with_middleware(contract_file)

	latest_block = eth_w3.eth.get_block_number()
	london_hard_fork_block_num = 12965000
	assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"

	n = 5
	for _ in range(n):
		block_num = random.randint(1, london_hard_fork_block_num - 1)
		ordered = is_ordered_block(block_num)
		if ordered:
			print(f"Block {block_num} is ordered")
		else:
			print(f"Block {block_num} is not ordered")

