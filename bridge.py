from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware  # Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
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
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info.")
        print("Please contact your instructor.")
        print(e)
        sys.exit(1)

    return contracts[chain]


def registerToken(token_address):
    """
    Registers the given token on the source chain and creates a wrapped token on the destination chain.
    """
    try:
        # Load contract information
        source_info = getContractInfo('source')
        destination_info = getContractInfo('destination')
    except Exception as e:
        print(f"Error loading contract info: {e}")
        return

    # Connect to Source and Destination chains
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

    # 1. Call registerToken() on Source contract
    try:
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
    except Exception as e:
        print(f"Failed to register token {token_address} on source chain: {e}")
        return

    # 2. Call createToken() on Destination contract
    try:
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
    except Exception as e:
        print(f"Failed to create wrapped token {token_address} on destination chain: {e}")


def createToken(token_address):
    """
    Calls the createToken function on the destination contract to create a wrapped token.

    Parameters:
        token_address (str): The address of the original token on the source chain.
    """
    try:
        # Load destination contract info
        destination_info = getContractInfo('destination')

        # Connect to the destination chain
        dest_w3 = connectTo(destination_chain)

        # Load the destination contract
        dest_contract = dest_w3.eth.contract(
            address=Web3.to_checksum_address(destination_info["address"]),
            abi=destination_info["abi"]
        )

        # Load private key for the destination chain
        DEST_PRIVATE_KEY = "0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0"
        dest_account = dest_w3.eth.account.from_key(DEST_PRIVATE_KEY)

        # Build the transaction
        nonce = dest_w3.eth.get_transaction_count(dest_account.address, 'pending')
        gas_price = dest_w3.eth.gas_price

        tx = dest_contract.functions.createToken(
            Web3.to_checksum_address(token_address)
        ).build_transaction({
            'from': dest_account.address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': gas_price,
            'chainId': dest_w3.eth.chain_id
        })

        # Sign and send the transaction
        signed_tx = dest_w3.eth.account.sign_transaction(tx, private_key=DEST_PRIVATE_KEY)
        tx_hash = dest_w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for the transaction to be confirmed
        receipt = dest_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Created wrapped token for {token_address}. TxHash: {tx_hash.hex()}, Block: {receipt.blockNumber}")

    except Exception as e:
        print(f"Failed to create wrapped token for {token_address}: {e}")


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
                dest_private_key = "0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0"  # Replace with your private key
                dest_account = dest_w3.eth.account.from_key(dest_private_key)

                tx = dest_contract.functions.wrap(token, recipient, amount).build_transaction({
                    'chainId': dest_w3.eth.chain_id,
                    'gas': 200000,
                    'gasPrice': dest_w3.eth.gas_price,
                    'nonce': dest_w3.eth.get_transaction_count(dest_account.address),
                })
                signed_tx = dest_w3.eth.account.sign_transaction(tx, private_key=dest_private_key)
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
                source_private_key = "0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070"  # Replace with your private key
                source_account = source_w3.eth.account.from_key(source_private_key)

                tx = source_contract.functions.withdraw(wrapped_token, recipient, amount).build_transaction({
                    'chainId': source_w3.eth.chain_id,
                    'gas': 200000,
                    'gasPrice': source_w3.eth.gas_price,
                    'nonce': source_w3.eth.get_transaction_count(source_account.address),
                })
                signed_tx = source_w3.eth.account.sign_transaction(tx, private_key=source_private_key)
                tx_hash = source_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f"Withdraw transaction sent: TxHash={tx_hash.hex()}")
        except Exception as e:
            print(f"Error processing Unwrap events: {e}")


if __name__ == "__main__":
    registerToken('0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c')
    createToken('0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c')

    