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
    Generate a stable private key
    challenge - byte string
    keyId (integer) - which key to use
    filename - filename to read and store mnemonics

    Each mnemonic is stored on a separate line
    If fewer than (keyId+1) mnemonics have been generated,
    generate a new one and return that
    """
    # Try to read existing mnemonics
    mnemonics = []
    try:
        with open(filename, 'r') as f:
            mnemonics = f.read().splitlines()
    except FileNotFoundError:
        pass

    # Generate new mnemonic if needed
    if keyId >= len(mnemonics):
        w3 = Web3()
        msg = eth_account.messages.encode_defunct(challenge)
        sig = eth_account.Account.sign_message(msg)
        eth_addr = sig.account_address

        # Store the new mnemonic
        with open(filename, 'a') as f:
            f.write(f"{sig.signature.hex()}\n")
        
        return sig, eth_addr
    else:
        # Use existing mnemonic
        stored_sig = bytes.fromhex(mnemonics[keyId])
        w3 = Web3()
        msg = eth_account.messages.encode_defunct(challenge)
        # Recreate signature and address from stored signature
        eth_addr = eth_account.Account.recover_message(msg,
                                                       signature=stored_sig)
        return stored_sig, eth_addr

# Test function
if __name__ == "__main__":
    for i in range(4):
        challenge = os.urandom(64)
        sig, addr = get_keys(challenge=challenge, keyId=i)
        print(addr)
