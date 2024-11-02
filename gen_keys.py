#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 22:57:16 2024

@author: hongchu
"""

from web3 import Web3
import eth_account
import os
from eth_account import Account
from eth_account.messages import encode_defunct

def get_keys(challenge, keyId=0, filename="eth_mnemonic.txt"):
    """
    Generate a stable private key.
    challenge - byte string
    keyId (integer) - which key to use
    filename - filename to read and store mnemonics

    Each mnemonic is stored on a separate line.
    If fewer than (keyId+1) mnemonics have been generated, generate a new one and return that.
    """
    w3 = Web3()

    # Ensure the file exists and read or generate mnemonics
    if not os.path.exists(filename):
        open(filename, 'w').close()

    with open(filename, 'r') as f:
        mnemonics = f.readlines()

    # Generate a new mnemonic if needed
    if keyId >= len(mnemonics):
        # Create a new account and get its private key (as hex string)
        new_account = Account.create()
        mnemonic = new_account.key.hex()  # Use the private key as a mnemonic in this example
        with open(filename, 'a') as f:
            f.write(mnemonic + '\n')
        account = Account.from_key(mnemonic)
    else:
        # Retrieve existing mnemonic
        mnemonic = mnemonics[keyId].strip()
        account = Account.from_key(mnemonic)

    # Generate an Ethereum address
    eth_addr = account.address

    # Encode the challenge message
    msg = encode_defunct(challenge)

    # Sign the challenge message
    sig = account.sign_message(msg)

    # Verify the signature by recovering the address
    assert eth_account.Account.recover_message(msg, signature=sig.signature) == eth_addr, "Failed to sign message properly"

    # Return the signature and Ethereum address
    return sig, eth_addr

# Test function
if __name__ == "__main__":
    for i in range(4):
        challenge = os.urandom(64)
        sig, addr = get_keys(challenge=challenge, keyId=i)
        print(addr)
