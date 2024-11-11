// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    using SafeERC20 for ERC20;

    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");

    mapping(address => address) public underlying_tokens; // Maps underlying token to wrapped token
    mapping(address => address) public wrapped_tokens;    // Maps wrapped token to underlying token
    address[] public tokens;                              // List of all registered underlying tokens

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed recipient, uint256 amount);
    event Unwrap(address indexed wrapped_token, address indexed underlying_token, address indexed recipient, uint256 amount);

    constructor(address admin) {
        require(admin != address(0), "Admin address cannot be zero");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

    /**
     * @dev Creates a wrapped token for the given underlying asset.
     * Can only be called by an address with CREATOR_ROLE.
     */
    function createToken(address _underlying_token, string memory name, string memory symbol) 
        public 
        onlyRole(CREATOR_ROLE) 
        returns (address) 
    {
        require(_underlying_token != address(0), "Invalid underlying token address");
        require(underlying_tokens[_underlying_token] == address(0), "Token already registered");

        // Deploy a new BridgeToken
        BridgeToken wrapped_token = new BridgeToken(_underlying_token, name, symbol, msg.sender);

        // Register the token mappings
        underlying_tokens[_underlying_token] = address(wrapped_token);
        wrapped_tokens[address(wrapped_token)] = _underlying_token;
        tokens.push(_underlying_token);

        emit Creation(_underlying_token, address(wrapped_token));
        return address(wrapped_token);
    }

    /**
     * @dev Wraps the specified amount of an underlying token into its corresponding wrapped token.
     * Can only be called by an address with WARDEN_ROLE.
     */
    function wrap(address _underlying_token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        require(_underlying_token != address(0), "Invalid underlying token address");
        require(_recipient != address(0), "Recipient cannot be zero address");
        require(_amount > 0, "Amount must be greater than zero");
        require(underlying_tokens[_underlying_token] != address(0), "Token not registered");

        address wrapped_token = underlying_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token not found");

        // Mint wrapped tokens to the recipient
        BridgeToken(wrapped_token).mint(_recipient, _amount);

        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);
    }

    /**
     * @dev Unwraps the specified amount of a wrapped token, burning it and preparing the underlying token for release.
     */
    function unwrap(address _wrapped_token, address _recipient, uint256 _amount) public {
        require(_wrapped_token != address(0), "Invalid wrapped token address");
        require(_recipient != address(0), "Recipient cannot be zero address");
        require(_amount > 0, "Amount must be greater than zero");
        require(wrapped_tokens[_wrapped_token] != address(0), "Token not registered");

        address underlying_token = wrapped_tokens[_wrapped_token];
        require(underlying_token != address(0), "Underlying token not found");

        // Burn the wrapped tokens
        BridgeToken(_wrapped_token).burnFrom(msg.sender, _amount);

        emit Unwrap(_wrapped_token, underlying_token, _recipient, _amount);
    }

    /**
     * @dev Returns the list of registered tokens.
     */
    function getTokens() public view returns (address[] memory) {
        return tokens;
    }
}
