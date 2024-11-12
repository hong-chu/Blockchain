// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");

    // Mapping from underlying token address to wrapped token address
    mapping(address => address) public underlying_tokens;

    // Mapping from wrapped token address to underlying token address
    mapping(address => address) public wrapped_tokens;

    // List of all wrapped token addresses
    address[] public tokens;

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address frm, address indexed to, uint256 amount);

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
        require(_underlying_token != address(0), "Invalid underlying token");
        require(underlying_tokens[_underlying_token] == address(0), "Token already exists");

        // Emit Creation event before token creation with wrapped_token as address(0)
        emit Creation(_underlying_token, address(0));

        // Deploy a new BridgeToken
        BridgeToken newToken = new BridgeToken(_underlying_token, name, symbol, address(this));

        // Update mappings
        underlying_tokens[_underlying_token] = address(newToken);
        wrapped_tokens[address(newToken)] = _underlying_token;

        // Add to tokens list
        tokens.push(address(newToken));

        return address(newToken);
    }
                        
    function wrap(
        address _underlying_token,
        address _recipient,
        uint256 _amount
    ) public onlyRole(WARDEN_ROLE) {
        require(_underlying_token != address(0), "Invalid underlying token");
        require(_recipient != address(0), "Recipient cannot be zero");
        require(_amount > 0, "Amount must be greater than zero");

        // Fetch the wrapped token associated with the underlying token
        address wrapped_token = underlying_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token not found");

        // Emit the Wrap event before minting
        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);

        // Mint the wrapped tokens to the recipient
        BridgeToken(wrapped_token).mint(_recipient, _amount);
    }
    
    function unwrap(
        address _wrapped_token,
        address _recipient,
        uint256 _amount
    ) public {
        require(_wrapped_token != address(0), "Invalid wrapped token");
        require(_recipient != address(0), "Recipient cannot be zero");
        require(_amount > 0, "Amount must be greater than zero");

        address underlying_token = wrapped_tokens[_wrapped_token];
        require(underlying_token != address(0), "Underlying token not found");

        BridgeToken token = BridgeToken(_wrapped_token);

        // Emit Unwrap event before burning
        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);

        // Burn the tokens from the sender's balance
        token.burn(_amount);
    }
}
