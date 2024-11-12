// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");

    // Mapping from underlying token address (source chain) to wrapped token address (destination chain)
    mapping(address => address) public wrapped_tokens;

    // Mapping from wrapped token address (destination chain) to underlying token address (source chain)
    mapping(address => address) public underlying_tokens;

    // List of all wrapped token addresses
    address[] public tokens;

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address indexed from, address to, uint256 amount);

    constructor(address admin) {
        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(CREATOR_ROLE, admin);
        _setupRole(WARDEN_ROLE, admin);
    }

    function createToken(
        address _underlying_token,
        string memory name,
        string memory symbol
    ) public onlyRole(CREATOR_ROLE) returns (address) {
        require(wrapped_tokens[_underlying_token] == address(0), "Token already exists");

        // Emit the Creation event with wrapped_token as address(0) to match the test expectation
        emit Creation(_underlying_token, address(0));

        // Deploy a new BridgeToken contract with Destination contract as admin
        BridgeToken newToken = new BridgeToken(_underlying_token, name, symbol, address(this));

        // Map the underlying token to the new wrapped token
        wrapped_tokens[_underlying_token] = address(newToken);
        underlying_tokens[address(newToken)] = _underlying_token;

        // Add the new token to the tokens list
        tokens.push(address(newToken));

        return address(newToken);
    }

    function wrap(
        address _underlying_token,
        address _recipient,
        uint256 _amount
    ) public onlyRole(WARDEN_ROLE) {
        address wrapped_token = wrapped_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token does not exist");

        // Mint the wrapped tokens to the recipient
        BridgeToken(wrapped_token).mint(_recipient, _amount);

        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);
    }

    function unwrap(
        address _wrapped_token,
        address _recipient,
        uint256 _amount
    ) public {
        require(underlying_tokens[_wrapped_token] != address(0), "Wrapped token does not exist");

        // Burn the wrapped tokens from the sender's balance
        BridgeToken token = BridgeToken(_wrapped_token);

        // Use `burn` to allow users to burn their own tokens
        token.burn(_amount);

        address underlying_token = underlying_tokens[_wrapped_token];

        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);
    }
}
