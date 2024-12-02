from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import csv
from datetime import datetime

eventfile = 'deposit_logs.csv'

def scanBlocks(chain, start_block, end_block, contract_address):
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError("Unsupported chain. Use 'avax' or 'bsc'.")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    DEPOSIT_ABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "token", "type": "address" }, { "indexed": true, "internalType": "address", "name": "recipient", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "Deposit", "type": "event" }]')
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print(f"Error: end_block ({end_block}) < start_block ({start_block})")
        return

    if end_block - start_block < 30:
        event_filter = contract.events.Deposit.create_filter(fromBlock=start_block, toBlock=end_block)
        events = event_filter.get_all_entries()
        with open(eventfile, mode='a', newline='') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(['Block Number', 'Timestamp', 'Transaction Hash', 'Token', 'Recipient', 'Amount'])
            for event in events:
                block_number = event['blockNumber']
                timestamp = datetime.utcfromtimestamp(w3.eth.get_block(block_number)['timestamp']).isoformat()
                tx_hash = event['transactionHash'].hex()  # Add transaction hash
                token = event['args']['token']
                recipient = event['args']['recipient']
                amount = event['args']['amount']
                writer.writerow([block_number, timestamp, tx_hash, token, recipient, amount])
                print(f"Logged event: Block {block_number}, Token {token}, Recipient {recipient}, Amount {amount}, TxHash {tx_hash}")
    else:
        for block_num in range(start_block, end_block + 1):
            event_filter = contract.events.Deposit.create_filter(fromBlock=block_num, toBlock=block_num)
            events = event_filter.get_all_entries()
            with open(eventfile, mode='a', newline='') as file:
                writer = csv.writer(file)
                if file.tell() == 0:
                    writer.writerow(['Block Number', 'Timestamp', 'Transaction Hash', 'Token', 'Recipient', 'Amount'])
                for event in events:
                    block_number = event['blockNumber']
                    timestamp = datetime.utcfromtimestamp(w3.eth.get_block(block_number)['timestamp']).isoformat()
                    tx_hash = event['transactionHash'].hex()  # Add transaction hash
                    token = event['args']['token']
                    recipient = event['args']['recipient']
                    amount = event['args']['amount']
                    writer.writerow([block_number, timestamp, tx_hash, token, recipient, amount])
                    print(f"Logged event: Block {block_number}, Token {token}, Recipient {recipient}, Amount {amount}, TxHash {tx_hash}")
