// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");

    mapping(address => address) public wrapped_tokens; // Maps underlying tokens to wrapped tokens
    mapping(address => address) public underlying_tokens; // Maps wrapped tokens to underlying tokens
    address[] public tokens; // List of registered tokens

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed recipient, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address indexed from, address to, uint256 amount);

    constructor(address admin) {
        require(admin != address(0), "Admin cannot be zero address");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

    /**
     * @dev Create a wrapped token for an underlying token.
     */
    function createToken(
        address _underlying_token,
        string memory name,
        string memory symbol
    ) public onlyRole(CREATOR_ROLE) returns (address) {
        require(_underlying_token != address(0), "Invalid underlying token");
        require(wrapped_tokens[_underlying_token] == address(0), "Token already exists");

        // Emit creation event with wrapped token set to address(0) initially
        emit Creation(_underlying_token, address(0));

        // Deploy a new BridgeToken
        BridgeToken newToken = new BridgeToken(_underlying_token, name, symbol, address(this));

        // Register mappings
        wrapped_tokens[_underlying_token] = address(newToken);
        underlying_tokens[address(newToken)] = _underlying_token;

        // Track the new wrapped token
        tokens.push(address(newToken));

        // Emit the actual creation event
        emit Creation(_underlying_token, address(newToken));
        return address(newToken);
    }

    /**
     * @dev Wrap tokens by minting the wrapped token to the recipient.
     */
    function wrap(
        address _underlying_token,
        address _recipient,
        uint256 _amount
    ) public onlyRole(WARDEN_ROLE) {
        require(_underlying_token != address(0), "Invalid underlying token");
        require(_recipient != address(0), "Recipient cannot be zero");
        require(_amount > 0, "Amount must be greater than zero");

        address wrapped_token = wrapped_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token does not exist");

        // Mint wrapped tokens
        BridgeToken(wrapped_token).mint(_recipient, _amount);

        // Emit wrap event
        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);
    }

    /**
     * @dev Unwrap tokens by burning the wrapped token and preparing to release the underlying asset.
     */
    function unwrap(
        address _wrapped_token,
        address _recipient,
        uint256 _amount
    ) public {
        require(_wrapped_token != address(0), "Invalid wrapped token");
        require(_recipient != address(0), "Recipient cannot be zero");
        require(_amount > 0, "Amount must be greater than zero");

        address underlying_token = underlying_tokens[_wrapped_token];
        require(underlying_token != address(0), "Underlying token not found");

        // Verify balance
        BridgeToken token = BridgeToken(_wrapped_token);
        require(token.balanceOf(msg.sender) >= _amount, "Insufficient balance");

        // Burn the wrapped tokens
        token.burnFrom(msg.sender, _amount);

        // Emit unwrap event
        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);
    }
}
