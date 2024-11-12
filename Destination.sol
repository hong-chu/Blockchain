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
        require(_underlying_token != address(0), "Underlying token address cannot be zero");
        require(wrapped_tokens[_underlying_token] == address(0), "Token already exists");
    
        // Deploy a new BridgeToken
        BridgeToken newToken = new BridgeToken(_underlying_token, name, symbol, address(this));
    
        // Register the new token
        address wrapped_token = address(newToken);
        wrapped_tokens[_underlying_token] = wrapped_token;
        underlying_tokens[wrapped_token] = _underlying_token;
        tokens.push(_underlying_token);
    
        // Emit the Creation event
        emit Creation(_underlying_token, wrapped_token);
    
        return wrapped_token;
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
        address wrapped_token = wrapped_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token does not exist");
    
        // Mint the wrapped tokens to the recipient
        BridgeToken(wrapped_token).mint(_recipient, _amount);
    
        // Emit the Wrap event with correct order
        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);
    }
    
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
    
        BridgeToken token = BridgeToken(_wrapped_token);
    
        // Ensure the caller has enough tokens to burn
        require(token.balanceOf(msg.sender) >= _amount, "Insufficient balance");
    
        // Burn the tokens from the sender's balance
        token.burnFrom(msg.sender, _amount);
    
        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);
    }

}
