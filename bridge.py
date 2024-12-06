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

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

    if chain in ['avax', 'bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # Inject the POA compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictionary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    return contracts[chain]

def scanAndBridge():
    """
        Scan both source and destination chains for events and perform the appropriate actions.
        Listens for 'Deposit' events on the source chain and calls 'wrap()' on the destination chain.
        Listens for 'Unwrap' events on the destination chain and calls 'withdraw()' on the source chain.
    """
    # Load contract info
    try:
        source_info = getContractInfo('source')
        destination_info = getContractInfo('destination')
    except Exception as e:
        print("Error loading contract info:", e)
        sys.exit(1)

    # Connect to chains
    source_w3 = connectTo(source_chain)
    dest_w3 = connectTo(destination_chain)

    # Load contracts
    source_contract = source_w3.eth.contract(
        address=source_info['address'],
        abi=source_info['abi']
    )
    dest_contract = dest_w3.eth.contract(
        address=destination_info['address'],
        abi=destination_info['abi']
    )

    # Fetch latest blocks for both chains
    source_latest_block = source_w3.eth.get_block_number()
    dest_latest_block = dest_w3.eth.get_block_number()

    # Listen for 'Deposit' events on the source chain
    deposit_events = source_contract.events.Deposit.create_filter(
        fromBlock=source_latest_block - 5, toBlock="latest"
    ).get_all_entries()

    for event in deposit_events:
        token = event.args['token']
        recipient = event.args['recipient']
        amount = event.args['amount']
        tx_hash = event.transactionHash.hex()

        print(f"Processing Deposit event: TxHash={tx_hash}, Token={token}, Recipient={recipient}, Amount={amount}")

        # Call wrap() on the destination chain
        wrap_tx = dest_contract.functions.wrap(token, recipient, amount).build_transaction({
            'chainId': dest_w3.eth.chain_id,
            'gas': 200000,
            'gasPrice': dest_w3.eth.gas_price,
            'nonce': dest_w3.eth.get_transaction_count(dest_w3.eth.account.privateKeyToAccount(destination_info['private_key']).address),
        })
        signed_wrap_tx = dest_w3.eth.account.sign_transaction(wrap_tx, private_key=destination_info['private_key'])
        wrap_tx_hash = dest_w3.eth.send_raw_transaction(signed_wrap_tx.rawTransaction)
        print(f"Wrap transaction sent: TxHash={wrap_tx_hash.hex()}")

    # Listen for 'Unwrap' events on the destination chain
    unwrap_events = dest_contract.events.Unwrap.create_filter(
        fromBlock=dest_latest_block - 5, toBlock="latest"
    ).get_all_entries()

    for event in unwrap_events:
        wrapped_token = event.args['wrapped_token']
        recipient = event.args['recipient']
        amount = event.args['amount']
        tx_hash = event.transactionHash.hex()

        print(f"Processing Unwrap event: TxHash={tx_hash}, WrappedToken={wrapped_token}, Recipient={recipient}, Amount={amount}")

        # Call withdraw() on the source chain
        withdraw_tx = source_contract.functions.withdraw(wrapped_token, recipient, amount).build_transaction({
            'chainId': source_w3.eth.chain_id,
            'gas': 200000,
            'gasPrice': source_w3.eth.gas_price,
            'nonce': source_w3.eth.get_transaction_count(source_w3.eth.account.privateKeyToAccount(source_info['private_key']).address),
        })
        signed_withdraw_tx = source_w3.eth.account.sign_transaction(withdraw_tx, private_key=source_info['private_key'])
        withdraw_tx_hash = source_w3.eth.send_raw_transaction(signed_withdraw_tx.rawTransaction)
        print(f"Withdraw transaction sent: TxHash={withdraw_tx_hash.hex()}")

if __name__ == "__main__":
    scanAndBridge()
