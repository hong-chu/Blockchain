import eth_account
import random
import string
import json
from pathlib import Path
from web3 import Web3
from web3.middleware import geth_poa_middleware  # Necessary for POA chains


def merkle_assignment():
    """
    Generates primes, builds a Merkle tree, signs a challenge, and optionally claims a prime.
    """
    # Generate the list of primes as integers
    num_of_primes = 8192
    primes = generate_primes(num_of_primes)

    # Convert primes to bytes32 format
    leaves = convert_leaves(primes)

    # Build the Merkle tree
    tree = build_merkle(leaves)

    # Select a random leaf to claim
    random_leaf_index = random.randint(1, len(leaves) - 1)
    print(f"Random Leaf Index: {random_leaf_index}")

    # Generate proof for the selected leaf
    proof = prove_merkle(tree, random_leaf_index)
    print(f"Merkle Proof: {[p.hex() for p in proof]}")

    # Generate and sign a challenge
    challenge = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    print(f"Challenge: {challenge}")

    addr, sig = sign_challenge(challenge)

    # Verify the signature before submitting
    if not sign_challenge_verify(challenge, addr, sig):
        print("Signature verification failed.")
        return None

    # Submit the Merkle proof and claim the prime
    try:
        tx_hash = send_signed_msg(proof, leaves[random_leaf_index])
        print(f"Transaction sent successfully! Hash: {tx_hash}")
        return tx_hash
    except Exception as e:
        print(f"Error submitting transaction: {e}")
        return None

def generate_primes(num_primes):
    """
        Function to generate the first 'num_primes' prime numbers
        returns list (with length n) of primes (as ints) in ascending order
    """
    primes_list = []
    candidate = 2  # Start with the first prime number

    while len(primes_list) < num_primes:
        # Check if the candidate is a prime number
        is_prime = all(candidate % p != 0 for p in primes_list if p * p <= candidate)
        if is_prime:
            primes_list.append(candidate)
        candidate += 1

    return primes_list


def convert_leaves(primes_list):
    """
        Converts the leaves (primes_list) to bytes32 format
        returns list of primes where list entries are bytes32 encodings of primes_list entries
    """
    # return [int.to_bytes(prime, 32, 'big') for prime in primes_list]
    return [prime.to_bytes(32, byteorder='big') for prime in primes_list]



def build_merkle(leaves):
    """
        Function to build a Merkle Tree from the list of prime numbers in bytes32 format
        Returns the Merkle tree (tree) as a list where tree[0] is the list of leaves,
        tree[1] is the parent hashes, and so on until tree[n] which is the root hash
        the root hash produced by the "hash_pair" helper function
    """

    tree = [leaves]  # Initialize tree with the leaves

    while len(tree[-1]) > 1:
        new_layer = []
        for i in range(0, len(tree[-1]), 2):
            new_layer.append(hash_pair(tree[-1][i], tree[-1][i+1]))
        tree.append(new_layer)
    
    return tree


def prove_merkle(merkle_tree, random_indx):
    """
        Takes a random_index to create a proof of inclusion for and a complete Merkle tree
        as a list of lists where index 0 is the list of leaves, index 1 is the list of
        parent hash values, up to index -1 which is the list of the root hash.
        returns a proof of inclusion as list of values
    """
    merkle_proof = []
    current_index = random_indx

    for layer in merkle_tree[:-1]:  # Exclude the root layer
        sibling_index = current_index ^ 1  # XOR to find sibling index
        if sibling_index < len(layer):
            merkle_proof.append(layer[sibling_index])
        current_index //= 2  # Move to the parent index in the next layer

    return merkle_proof


def sign_challenge(challenge):
    """
        Takes a challenge (string)
        Returns address, sig
        where address is an ethereum address and sig is a signature (in hex)
        This method is to allow the auto-grader to verify that you have
        claimed a prime
    """
    acct = get_account()

    addr = acct.address
    eth_sk = acct.key

    eth_sig_obj = acct.sign_message(eth_account.messages.encode_defunct(text=challenge))

    return addr, eth_sig_obj.signature.hex()

    
def send_signed_msg(proof, random_leaf):
    """
    Submits the Merkle proof and claims the prime on the contract.
    """
    chain = 'bsc'

    # Load account and contract information
    acct = get_account()
    address, abi = get_contract_info(chain)
    w3 = connect_to(chain)

    # Create contract instance
    contract = w3.eth.contract(address=address, abi=abi)

    # Validate inputs
    assert isinstance(random_leaf, bytes) and len(random_leaf) == 32, "random_leaf must be bytes32"
    assert all(isinstance(p, bytes) and len(p) == 32 for p in proof), "Proof elements must be bytes32"

    # Debugging prints
    print(f"Submitting Merkle Proof: {[p.hex() for p in proof]}")
    print(f"Submitting Leaf: {random_leaf.hex()}")

    # Estimate gas
    try:
        estimated_gas = contract.functions.submit(proof, random_leaf).estimate_gas({
            'from': acct.address
        })
    except Exception as e:
        print(f"Error estimating gas: {e}")
        return None

    # Build transaction
    tx = contract.functions.submit(proof, random_leaf).build_transaction({
        'chainId': w3.eth.chain_id,
        'from': acct.address,
        'nonce': w3.eth.get_transaction_count(acct.address),
        'gas': estimated_gas,
        'gasPrice': w3.eth.gas_price
    })

    # Sign and send transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=acct.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    print(f"Transaction sent with hash: {tx_hash.hex()}")
    return tx_hash



# Helper functions that do not need to be modified
def connect_to(chain):
    """
        Takes a chain ('avax' or 'bsc') and returns a web3 instance
        connected to that chain.
    """
    if chain not in ['avax','bsc']:
        print(f"{chain} is not a valid option for 'connect_to()'")
        return None
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    else:
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    w3 = Web3(Web3.HTTPProvider(api_url))
    # inject the poa compatibility middleware to the innermost layer
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    return w3


def get_account():
    """
        Returns an account object recovered from the secret key
        in "sk.txt"
    """
    cur_dir = Path(__file__).parent.absolute()
    with open(cur_dir.joinpath('sk.txt'), 'r') as f:
        sk = f.readline().rstrip()
    if sk[0:2] == "0x":
        sk = sk[2:]
    return eth_account.Account.from_key(sk)


def get_contract_info(chain):
    """
        Returns a contract address and contract abi from "contract_info.json"
        for the given chain
    """
    cur_dir = Path(__file__).parent.absolute()
    with open(cur_dir.joinpath("contract_info.json"), "r") as f:
        d = json.load(f)
        d = d[chain]
    return d['address'], d['abi']


def sign_challenge_verify(challenge, addr, sig):
    """
        Helper to verify signatures, verifies sign_challenge(challenge)
        the same way the grader will. No changes are needed for this method
    """
    eth_encoded_msg = eth_account.messages.encode_defunct(text=challenge)

    if eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == addr:
        print(f"Success: signed the challenge {challenge} using address {addr}!")
        return True
    else:
        print(f"Failure: The signature does not verify!")
        print(f"signature = {sig}\naddress = {addr}\nchallenge = {challenge}")
        return False


def hash_pair(a, b):
    """
        The OpenZeppelin Merkle Tree Validator we use sorts the leaves
        https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/utils/cryptography/MerkleProof.sol#L217
        So you must sort the leaves as well

        Also, hash functions like keccak are very sensitive to input encoding, so the solidity_keccak function is the function to use

        Another potential gotcha, if you have a prime number (as an int) bytes(prime) will *not* give you the byte representation of the integer prime
        Instead, you must call int.to_bytes(prime,'big').
    """
    if a < b:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [a, b])
    else:
        return Web3.solidity_keccak(['bytes32', 'bytes32'], [b, a])


if __name__ == "__main__":
    merkle_assignment()
