#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 10:58:35 2024

@author: hongchu
"""

from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware #Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( "Failed to read contract info" )
        print( "Please contact your instructor" )
        print( e )
        sys.exit(1)

    return contracts[chain]



def scanBlocks(chain):
    """
    chain - (string) should be either "source" or "destination"
    Scan the last 5 blocks of the source and destination chains
    Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
    When Deposit events are found on the source chain, call the 'wrap' function the destination chain
    When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    # Load contract info
    contract_info = getContractInfo(chain)

    # Connect to the specified chain
    w3 = connectTo(chain)
    target_chain = destination_chain if chain == 'source' else source_chain
    target_w3 = connectTo(target_chain)

    contract = w3.eth.contract(address=contract_info['address'], abi=contract_info['abi'])
    target_contract_info = getContractInfo(target_chain)
    target_contract = target_w3.eth.contract(address=target_contract_info['address'], abi=target_contract_info['abi'])

    # Determine the event and function to handle
    event_name = 'Deposit' if chain == 'source' else 'Unwrap'
    target_function = 'wrap' if chain == 'source' else 'withdraw'

    # Scan the last 5 blocks
    latest_block = w3.eth.get_block_number()
    start_block = max(0, latest_block - 5)
    end_block = latest_block

    print(f"Scanning {event_name} events on {chain} from blocks {start_block} to {end_block}...")

    try:
        # Filter and process events
        event_filter = getattr(contract.events, event_name).create_filter(
            fromBlock=start_block, toBlock=end_block
        )
        events = event_filter.get_all_entries()

        for event in events:
            args = event["args"]
            transaction_hash = event["transactionHash"].hex()
            token = args.get("token")
            recipient = args.get("recipient")
            amount = args.get("amount")

            print(f"{event_name} Event: Token {token}, Recipient {recipient}, Amount {amount}, TxHash {transaction_hash}")

            # Call the appropriate function on the target chain
            if target_function == 'wrap':
                target_contract.functions.wrap(token, recipient, amount).transact(
                    {"from": target_w3.eth.default_account}
                )
                print(f"Called wrap on {target_chain} for {amount} tokens to {recipient}.")
            elif target_function == 'withdraw':
                target_contract.functions.withdraw(token, recipient, amount).transact(
                    {"from": target_w3.eth.default_account}
                )
                print(f"Called withdraw on {target_chain} for {amount} tokens to {recipient}.")
    except Exception as e:
        print(f"Error scanning blocks: {e}")
