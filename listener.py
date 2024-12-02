from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import csv
from datetime import datetime
import pandas as pd

eventfile = 'deposit_logs.csv'

def scanBlocks(chain, start_block, end_block, contract_address):
    """
    Scans the blockchain for Deposit events and writes them to 'deposit_logs.csv'.
    """
    # RPC endpoints
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    else:
        raise ValueError("Unsupported chain. Choose either 'avax' or 'bsc'.")

    # Set up Web3 connection
    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # For POA chains

    # Define the ABI for the Deposit event
    DEPOSIT_ABI = json.loads(
        '[{"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "token", "type": "address"}, {"indexed": true, "internalType": "address", "name": "recipient", "type": "address"}, {"indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "Deposit", "type": "event"}]'
    )

    # Set up the contract
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    # Fetch events from the blockchain
    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    # Initialize list for storing event data
    all_events = []

    # Scan blocks for events
    print(f"Scanning blocks {start_block} to {end_block} on {chain}.")
    event_filter = contract.events.Deposit.create_filter(fromBlock=start_block, toBlock=end_block)
    events = event_filter.get_all_entries()

    # Process each event
    for event in events:
        block_number = event["blockNumber"]
        transaction_hash = event["transactionHash"].hex()
        token = event["args"]["token"]
        recipient = event["args"]["recipient"]
        amount = event["args"]["amount"]
        contract_address = event["address"]

        # Log event
        print(
            f"Logged event: Block {block_number}, Token {token}, Recipient {recipient}, Amount {amount}, TxHash {transaction_hash}"
        )

        # Append the event data to the list
        all_events.append(
            {
                "chain": chain,
                "token": token,
                "recipient": recipient,
                "amount": amount,
                "transactionHash": transaction_hash,
                "address": contract_address,
            }
        )

    # Write data to CSV
    df = pd.DataFrame(all_events)
    df.to_csv(eventfile, index=False, mode='a', header=not pd.read_csv(eventfile).empty)
