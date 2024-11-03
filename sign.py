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
    # your code here

    eth_address = '0x01a6Bb89B07C00273658EDf65bf2a2Aa5E6e33d3'  # Eth account
    private_key = '0x1860b0c86a901ab4e4ef4338338d884da3486abbe5f13a4cb9ac7bc61346a070'
    account = eth_account.Account.from_key(private_key)

    # generate signature
    # your code here

    # Prepare the message for signing
    message = encode_defunct(text=m)

    # Generate the signature
    signed_message = account.sign_message(message)
    eth_address = account.address
    assert isinstance(signed_message, eth_account.datastructures.SignedMessage)

    return eth_address, signed_message
