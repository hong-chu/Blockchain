#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  7 17:19:29 2024

@author: hongchu
"""

import csv
import os
import sys
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import geth_poa_middleware  # Necessary for POA chains

# Configuration
SOURCE_CHAIN = 'avax'
DESTINATION_CHAIN = 'bsc'
CONTRACT_INFO_FILE = "contract_info.json"
ERC20_CSV_FILE = "erc20s.csv"

def connect_to(chain):
    """
    Connect to the specified blockchain network.
    """
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    else:
        raise ValueError(f"Unsupported chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))
    # Inject the PoA compatibility middleware
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {chain} chain.")
    return w3

def get_contract_info(chain):
    """
    Load the contract_info file into a dictionary.
    """
    p = Path(__file__).with_name(CONTRACT_INFO_FILE)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract_info.json.")
        print("Please ensure the file exists and is correctly formatted.")
        print(e)
        sys.exit(1)

    if chain not in contracts:
        print(f"Chain '{chain}' not found in contract_info.json.")
        sys.exit(1)

    return contracts[chain]

def register_and_create_tokens(source_w3, dest_w3, source_contract, dest_contract, source_account, dest_account, tokens):
    """
    Register tokens on the Source contract and create wrapped tokens on the Destination contract.
    """
    for chain, token_address in tokens:
        if chain == "avax":
            print(f"\nProcessing token {token_address} on {SOURCE_CHAIN.upper()} chain.")

            # 1. Call registerToken() on Source contract
            try:
                # Build the transaction
                register_tx = source_contract.functions.registerToken(token_address).build_transaction({
                    'from': source_account.address,
                    'nonce': source_w3.eth.get_transaction_count(source_account.address, 'pending'),
                    'gas': 200000,
                    'gasPrice': source_w3.eth.gas_price,
                    'chainId': source_w3.eth.chain_id
                })

                # Sign the transaction
                signed_register_tx = source_account.sign_transaction(register_tx)

                # Send the transaction
                register_tx_hash = source_w3.eth.send_raw_transaction(signed_register_tx.rawTransaction)
                print(f"Registered token {token_address} on Source contract. TxHash: {register_tx_hash.hex()}")

                # Wait for the transaction receipt
                register_receipt = source_w3.eth.wait_for_transaction_receipt(register_tx_hash)
                if register_receipt.status != 1:
                    print(f"Transaction failed: {register_tx_hash.hex()}")
                    continue
                else:
                    print(f"Registration successful for token {token_address}.")

            except Exception as e:
                print(f"Error registering token {token_address} on Source contract: {e}")
                continue

            # 2. Call createToken() on Destination contract
            try:
                # Optional: Fetch underlying token details (name and symbol)
                underlying_contract = dest_w3.eth.contract(address=token_address, abi=[
                    {
                        "constant": True,
                        "inputs": [],
                        "name": "name",
                        "outputs": [{"name": "", "type": "string"}],
                        "type": "function"
                    },
                    {
                        "constant": True,
                        "inputs": [],
                        "name": "symbol",
                        "outputs": [{"name": "", "type": "string"}],
                        "type": "function"
                    }
                ])

                try:
                    underlying_name = underlying_contract.functions.name().call()
                    underlying_symbol = underlying_contract.functions.symbol().call()
                except Exception:
                    # Fallback if name or symbol functions are not available
                    underlying_name = "Unknown"
                    underlying_symbol = "UNK"

                wrapped_name = f"Wrapped {underlying_name}"
                wrapped_symbol = f"W{underlying_symbol}"

                # Build the transaction
                create_tx = dest_contract.functions.createToken(token_address, wrapped_name, wrapped_symbol).build_transaction({
                    'from': dest_account.address,
                    'nonce': dest_w3.eth.get_transaction_count(dest_account.address, 'pending'),
                    'gas': 200000,
                    'gasPrice': dest_w3.eth.gas_price,
                    'chainId': dest_w3.eth.chain_id
                })

                # Sign the transaction
                signed_create_tx = dest_account.sign_transaction(create_tx)

                # Send the transaction
                create_tx_hash = dest_w3.eth.send_raw_transaction(signed_create_tx.rawTransaction)
                print(f"Created wrapped token for {token_address} on Destination contract. TxHash: {create_tx_hash.hex()}")

                # Wait for the transaction receipt
                create_receipt = dest_w3.eth.wait_for_transaction_receipt(create_tx_hash)
                if create_receipt.status != 1:
                    print(f"Transaction failed: {create_tx_hash.hex()}")
                    continue
                else:
                    print(f"Wrapped token creation successful for token {token_address}.")

            except Exception as e:
                print(f"Error creating wrapped token for {token_address} on Destination contract: {e}")
                continue

def main():
    # Load contract information
    source_info = get_contract_info('source')
    destination_info = get_contract_info('destination')

    # Connect to both chains
    try:
        source_w3 = connect_to(SOURCE_CHAIN)
        dest_w3 = connect_to(DESTINATION_CHAIN)
    except Exception as e:
        print(e)
        sys.exit(1)

    # Load Source and Destination contracts
    source_contract = source_w3.eth.contract(
        address=Web3.to_checksum_address(source_info["address"]),
        abi=source_info["abi"]
    )

    dest_contract = dest_w3.eth.contract(
        address=Web3.to_checksum_address(destination_info["address"]),
        abi=destination_info["abi"]
    )

    # Load private keys securely (using environment variables is recommended)
    SOURCE_PRIVATE_KEY = os.getenv("SOURCE_PRIVATE_KEY", "0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070")
    DEST_PRIVATE_KEY = os.getenv("DEST_PRIVATE_KEY", "0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0")

    if not SOURCE_PRIVATE_KEY or not DEST_PRIVATE_KEY:
        print("Please set SOURCE_PRIVATE_KEY and DEST_PRIVATE_KEY environment variables.")
        sys.exit(1)

    # Initialize accounts
    try:
        source_account = source_w3.eth.account.from_key(SOURCE_PRIVATE_KEY)
        dest_account = dest_w3.eth.account.from_key(DEST_PRIVATE_KEY)
    except Exception as e:
        print(f"Error loading accounts: {e}")
        sys.exit(1)

    # Ensure that the accounts have the necessary roles
    try:
        # Check ADMIN_ROLE on Source contract
        ADMIN_ROLE = source_contract.functions.ADMIN_ROLE().call()
        has_admin = source_contract.functions.hasRole(ADMIN_ROLE, source_account.address).call()
        if not has_admin:
            print(f"Account {source_account.address} does not have ADMIN_ROLE on Source contract.")
            sys.exit(1)

        # Check CREATOR_ROLE on Destination contract
        CREATOR_ROLE = dest_contract.functions.CREATOR_ROLE().call()
        has_creator = dest_contract.functions.hasRole(CREATOR_ROLE, dest_account.address).call()
        if not has_creator:
            print(f"Account {dest_account.address} does not have CREATOR_ROLE on Destination contract.")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking roles: {e}")
        sys.exit(1)

    # Read ERC20 tokens from CSV
    tokens = []
    try:
        with open(ERC20_CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                chain = row['chain'].strip().lower()
                token_address = row['address'].strip()
                tokens.append((chain, Web3.to_checksum_address(token_address)))
    except FileNotFoundError:
        print(f"File {ERC20_CSV_FILE} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {ERC20_CSV_FILE}: {e}")
        sys.exit(1)

    # Register and create tokens
    register_and_create_tokens(
        source_w3, dest_w3,
        source_contract, dest_contract,
        source_account, dest_account,
        tokens
    )

    # Optionally, you can add scanning of blocks here or in a separate script
    # scanBlocks('source')
    # scanBlocks('destination')

if __name__ == "__main__":
    main()
