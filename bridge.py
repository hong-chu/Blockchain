import csv
import os
import sys
import json
from pathlib import Path
from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware  # Necessary for POA chains

# Chain configurations
source_chain = 'avax'
destination_chain = 'bsc'
contract_info_file = "contract_info.json"
erc20_csv_file = "erc20s.csv"

def connectTo(chain):
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    else:
        raise ValueError(f"Unsupported chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))
    # Inject the PoA compatibility middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
    Load the contract_info file into a dictionary.
    """
    p = Path(__file__).with_name(contract_info_file)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info.")
        print("Please contact your instructor.")
        print(e)
        sys.exit(1)

    return contracts[chain]

def registerTokens():
    """
    Reads ERC20 tokens from a CSV file and registers them on the source chain,
    and creates corresponding wrapped tokens on the destination chain.
    """
    tokens = []

    # Read ERC20 tokens from CSV
    with open(erc20_csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            chain = row['chain'].strip().lower()
            token_address = row['address'].strip()
            tokens.append((chain, Web3.to_checksum_address(token_address)))

    try:
        # Load contract information
        source_info = getContractInfo('source')
        destination_info = getContractInfo('destination')
    except Exception as e:
        print(f"Error loading contract info: {e}")
        return

    # Connect to Source and Destination
    source_w3 = connectTo(source_chain)
    dest_w3 = connectTo(destination_chain)

    # Load contracts
    source_contract = source_w3.eth.contract(
        address=Web3.to_checksum_address(source_info["address"]),
        abi=source_info["abi"]
    )

    dest_contract = dest_w3.eth.contract(
        address=Web3.to_checksum_address(destination_info["address"]),
        abi=destination_info["abi"]
    )

    # Load private keys (ensure these are securely stored)
    SOURCE_PRIVATE_KEY = "0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070"
    DEST_PRIVATE_KEY = "0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0"

    source_account = source_w3.eth.account.from_key(SOURCE_PRIVATE_KEY)
    source_address_checksum = source_account.address

    dest_account = dest_w3.eth.account.from_key(DEST_PRIVATE_KEY)
    dest_address_checksum = dest_account.address

    for chain_name, token_address in tokens:
        if chain_name == "avax":
            # 1. Call registerToken() on Source contract
            source_nonce = source_w3.eth.get_transaction_count(source_address_checksum, 'pending')
            gas_price = source_w3.eth.gas_price

            register_tx = source_contract.functions.registerToken(token_address).build_transaction({
                'from': source_address_checksum,
                'nonce': source_nonce,
                'gas': 200000,
                'gasPrice': gas_price,
                'chainId': source_w3.eth.chain_id
            })

            signed_register_tx = source_w3.eth.account.sign_transaction(register_tx, private_key=SOURCE_PRIVATE_KEY)
            register_tx_hash = source_w3.eth.send_raw_transaction(signed_register_tx.rawTransaction)
            source_w3.eth.wait_for_transaction_receipt(register_tx_hash)
            print(f"Registered token {token_address} on source contract. TxHash: {register_tx_hash.hex()}")

            # 2. Call createToken() on Destination contract
            # Provide a name and symbol for the wrapped token
            wrapped_name = f"Wrapped {token_address[:6]}"
            wrapped_symbol = f"W{token_address[:3].upper()}"

            dest_nonce = dest_w3.eth.get_transaction_count(dest_address_checksum, 'pending')
            dest_gas_price = dest_w3.eth.gas_price

            create_tx = dest_contract.functions.createToken(token_address, wrapped_name, wrapped_symbol).build_transaction({
                'from': dest_address_checksum,
                'nonce': dest_nonce,
                'gas': 200000,
                'gasPrice': dest_gas_price,
                'chainId': dest_w3.eth.chain_id
            })

            signed_create_tx = dest_w3.eth.account.sign_transaction(create_tx, private_key=DEST_PRIVATE_KEY)
            create_tx_hash = dest_w3.eth.send_raw_transaction(signed_create_tx.rawTransaction)
            dest_w3.eth.wait_for_transaction_receipt(create_tx_hash)
            print(f"Created wrapped token for {token_address} on destination contract. TxHash: {create_tx_hash.hex()}")

def scanBlocks(chain):
    """
    Scans the last 5 blocks of the specified chain for events and responds accordingly.
    """
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    try:
        # Load contract information
        source_info = getContractInfo('source')
        destination_info = getContractInfo('destination')
    except Exception as e:
        print(f"Error loading contract info: {e}")
        return

    # Connect to the respective chain
    w3 = connectTo(source_chain if chain == "source" else destination_chain)

    # Load contract
    contract_info = source_info if chain == "source" else destination_info
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_info["address"]),
        abi=contract_info["abi"]
    )

    # Fetch latest block number
    latest_block = w3.eth.get_block_number()

    # Load private keys
    SOURCE_PRIVATE_KEY = "0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070"
    DEST_PRIVATE_KEY = "0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0"

    if chain == "source":
        # Look for 'Deposit' events
        try:
            events = contract.events.Deposit.create_filter(
                fromBlock=max(latest_block - 5, 1), toBlock="latest"
            ).get_all_entries()

            for event in events:
                token = event.args['token']
                recipient = event.args['recipient']
                amount = event.args['amount']
                print(f"Deposit Event - Token: {token}, Recipient: {recipient}, Amount: {amount}")

                # Call wrap() on the destination chain
                dest_w3 = connectTo(destination_chain)
                dest_contract = dest_w3.eth.contract(
                    address=Web3.to_checksum_address(destination_info["address"]),
                    abi=destination_info["abi"]
                )
                private_key = DEST_PRIVATE_KEY
                if not private_key:
                    print("Destination private key not found.")
                    return
                account = dest_w3.eth.account.from_key(private_key)

                tx = dest_contract.functions.wrap(token, recipient, amount).build_transaction({
                    'chainId': dest_w3.eth.chain_id,
                    'gas': 200000,
                    'gasPrice': dest_w3.eth.gas_price,
                    'nonce': dest_w3.eth.get_transaction_count(account.address),
                })
                signed_tx = dest_w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = dest_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"Wrap transaction sent: TxHash={tx_hash.hex()}")
        except Exception as e:
            print(f"Error processing Deposit events: {e}")

    elif chain == "destination":
        # Look for 'Unwrap' events
        try:
            events = contract.events.Unwrap.create_filter(
                fromBlock=max(latest_block - 5, 1), toBlock="latest"
            ).get_all_entries()

            for event in events:
                wrapped_token = event.args['wrapped_token']
                recipient = event.args['to']
                amount = event.args['amount']
                print(f"Unwrap Event - WrappedToken: {wrapped_token}, Recipient: {recipient}, Amount: {amount}")

                # Call withdraw() on the source chain
                source_w3 = connectTo(source_chain)
                source_contract = source_w3.eth.contract(
                    address=Web3.to_checksum_address(source_info["address"]),
                    abi=source_info["abi"]
                )
                private_key = SOURCE_PRIVATE_KEY
                if not private_key:
                    print("Source private key not found.")
                    return
                account = source_w3.eth.account.from_key(private_key)

                tx = source_contract.functions.withdraw(wrapped_token, recipient, amount).build_transaction({
                    'chainId': source_w3.eth.chain_id,
                    'gas': 200000,
                    'gasPrice': source_w3.eth.gas_price,
                    'nonce': source_w3.eth.get_transaction_count(account.address),
                })
                signed_tx = source_w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = source_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"Withdraw transaction sent: TxHash={tx_hash.hex()}")
        except Exception as e:
            print(f"Error processing Unwrap events: {e}")

if __name__ == "__main__":
    # Step 1: Register tokens and create wrapped tokens
    registerTokens()

    # Step 2: Start scanning blocks for events
    scanBlocks('source')
    scanBlocks('destination')
