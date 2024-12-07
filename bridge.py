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

    # Create filters for events
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
                private_key = '0x9ead96f0d944bb419abaf49efa5f54a77a37754f398651c984eb156a867327e0'
                if not private_key:
                    print("Destination private key not found.")
                    return
                account = dest_w3.eth.account.privateKeyToAccount(private_key)

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
                private_key = '0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070'
                if not private_key:
                    print("Source private key not found.")
                    return
                account = source_w3.eth.account.privateKeyToAccount(private_key)

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
