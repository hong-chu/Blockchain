from web3 import Web3
from web3.middleware import geth_poa_middleware  # Necessary for POA chains
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"

def connectTo(chain):
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    else:
        raise ValueError(f"Unsupported chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)  # Inject PoA compatibility middleware
    return w3

def getContractInfo(chain):
    """
    Load the contract_info file into a dictionary.
    """
    try:
        with open(contract_info, 'r') as f:
            contracts = json.load(f)
        return contracts[chain]
    except Exception as e:
        print("Failed to read contract info:", e)
        sys.exit(1)

def wrap(token, recipient, amount):
    """
    Calls the wrap function on the destination contract.
    """
    try:
        # Load destination contract info
        dest_info = getContractInfo('destination')
        dest_w3 = connectTo(destination_chain)
        dest_contract = dest_w3.eth.contract(
            address=Web3.to_checksum_address(dest_info['address']),
            abi=dest_info['abi']
        )

        # Load destination private key
        DEST_PRIVATE_KEY = "0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0"
        dest_account = dest_w3.eth.account.from_key(DEST_PRIVATE_KEY)

        # Build and send the wrap transaction
        tx = dest_contract.functions.wrap(
            Web3.to_checksum_address(token),
            Web3.to_checksum_address(recipient),
            amount
        ).build_transaction({
            'from': dest_account.address,
            'nonce': dest_w3.eth.get_transaction_count(dest_account.address, 'pending'),
            'gas': 500_000,  # Adjust gas if needed
            'gasPrice': dest_w3.eth.gas_price,
            'chainId': dest_w3.eth.chain_id,
        })
        signed_tx = dest_w3.eth.account.sign_transaction(tx, private_key=DEST_PRIVATE_KEY)
        tx_hash = dest_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = dest_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Wrap transaction successful. TxHash: {tx_hash.hex()}, Block: {receipt.blockNumber}")
    except Exception as e:
        print(f"Failed to send wrap transaction: {e}")

def withdraw(wrapped_token, recipient, amount):
    """
    Calls the withdraw function on the source contract to release the original tokens.
    """
    try:
        # Load source contract info
        source_info = getContractInfo('source')
        source_w3 = connectTo(source_chain)
        source_contract = source_w3.eth.contract(
            address=Web3.to_checksum_address(source_info['address']),
            abi=source_info['abi']
        )

        # Load source private key
        SOURCE_PRIVATE_KEY = "0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070"
        source_account = source_w3.eth.account.from_key(SOURCE_PRIVATE_KEY)

        # Build and send the withdraw transaction
        tx = source_contract.functions.withdraw(
            Web3.to_checksum_address(wrapped_token),
            Web3.to_checksum_address(recipient),
            amount
        ).build_transaction({
            'from': source_account.address,
            'nonce': source_w3.eth.get_transaction_count(source_account.address, 'pending'),
            'gas': 500_000,  # Adjust gas if needed
            'gasPrice': source_w3.eth.gas_price,
            'chainId': source_w3.eth.chain_id
        })
        signed_tx = source_w3.eth.account.sign_transaction(tx, private_key=SOURCE_PRIVATE_KEY)
        tx_hash = source_w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = source_w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Withdraw transaction successful. TxHash: {tx_hash.hex()}, Block: {receipt.blockNumber}")
    except Exception as e:
        print(f"Failed to send withdraw transaction: {e}")

def scanBlocks(chain):
    """
    Scans the last 5 blocks for events and responds accordingly.
    """
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return

    try:
        # Load contract info
        contract_info = getContractInfo(chain)
        w3 = connectTo(source_chain if chain == 'source' else destination_chain)
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_info['address']),
            abi=contract_info['abi']
        )

        # Fetch latest block number
        latest_block = w3.eth.get_block_number()
        print(f"Scanning blocks {max(latest_block - 5, 1)} to {latest_block} on {chain} chain...")

        if chain == 'source':
            # Listen for Deposit events
            events = contract.events.Deposit.create_filter(
                fromBlock=max(latest_block - 5, 1),
                toBlock='latest'
            ).get_all_entries()
            for event in events:
                token = event.args['token']
                recipient = event.args['recipient']
                amount = event.args['amount']
                print(f"Deposit Event - Token: {token}, Recipient: {recipient}, Amount: {amount}")
                wrap(token, recipient, amount)
        elif chain == 'destination':
            # Listen for Unwrap events
            events = contract.events.Unwrap.create_filter(
                fromBlock=max(latest_block - 5, 1),
                toBlock='latest'
            ).get_all_entries()
            for event in events:
                wrapped_token = event.args['wrapped_token']
                recipient = event.args['to']
                amount = event.args['amount']
                print(f"Unwrap Event - WrappedToken: {wrapped_token}, Recipient: {recipient}, Amount: {amount}")
                withdraw(wrapped_token, recipient, amount)
    except Exception as e:
        print(f"Failed to scan blocks on {chain} chain: {e}")

# if __name__ == "__main__":
#     scanBlocks('source')
#     scanBlocks('destination')
