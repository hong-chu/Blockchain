#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 23:37:43 2024

@author: hongchu
"""

import eth_account
from web3 import Web3
from eth_account.messages import encode_defunct


def sign(m):
    w3 = Web3()
    # create an eth account and recover the address (derived from the public key) and private key
    # Create an Ethereum account with a new private key
    account = eth_account.Account.create()
    eth_address = account.address  # Derived Ethereum address
    private_key = account.key.hex()  # Private key in hexadecimal format

    # Prepare the message for signing
    message = encode_defunct(text=m)

    # Sign the message
    signed_message = account.sign_message(message)

    # Verify that the signed message is indeed a SignedMessage object
    assert isinstance(signed_message, eth_account.datastructures.SignedMessage), "Signing failed."

    return eth_address, signed_message
