from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import csv
from datetime import datetime

eventfile = 'deposit_logs.csv'

def scanBlocks(chain, start_block, end_block, contract_address):
    """
    Reads "Deposit" events from the specified contract and writes information
    about the events to the file "deposit_logs.csv".
    """
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    else:
        w3 = Web3(Web3.HTTPProvider(api_url))

    DEPOSIT_ABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "token", "type": "address" }, { "indexed": true, "internalType": "address", "name": "recipient", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "Deposit", "type": "event" }]')
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    arg_filter = {}

    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print(f"Error end_block < start_block!")
        print(f"end_block = {end_block}")
        print(f"start_block = {start_block}")

    if start_block == end_block:
        print(f"Scanning block {start_block} on {chain}")
    else:
        print(f"Scanning blocks {start_block} - {end_block} on {chain}")

    if end_block - start_block < 30:
        event_filter = contract.events.Deposit.create_filter(fromBlock=start_block, toBlock=end_block, argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        # Extract and log events
        for event in events:
            block = event["blockNumber"]
            tx_hash = event["transactionHash"].hex()  # Ensure this is converted to a string
            token = event["args"]["token"]
            recipient = event["args"]["recipient"]
            amount = event["args"]["amount"]

            timestamp = w3.eth.get_block(block)["timestamp"]
            timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()

            with open(eventfile, "a") as f:
                f.write(f"{block},{timestamp_iso},{token},{recipient},{amount},{tx_hash}\n")
    else:
        for block_num in range(start_block, end_block + 1):
            event_filter = contract.events.Deposit.create_filter(fromBlock=block_num, toBlock=block_num, argument_filters=arg_filter)
            events = event_filter.get_all_entries()
            # Extract and log events
            for event in events:
                block = event["blockNumber"]
                tx_hash = event["transactionHash"].hex()  # Ensure this is converted to a string
                token = event["args"]["token"]
                recipient = event["args"]["recipient"]
                amount = event["args"]["amount"]

                timestamp = w3.eth.get_block(block)["timestamp"]
                timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()

                with open(eventfile, "a") as f:
                    f.write(f"{block},{timestamp_iso},{token},{recipient},{amount},{tx_hash}\n")
