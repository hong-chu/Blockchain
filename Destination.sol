// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");

    // Mapping from underlying token to wrapped token
    mapping(address => address) public wrapped_tokens;

    // Mapping from wrapped token to underlying token
    mapping(address => address) public underlying_tokens;

    // List of registered underlying tokens
    address[] public tokens;

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed recipient, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address indexed sender, address recipient, uint256 amount);

    constructor(address admin) {
        require(admin != address(0), "Admin cannot be zero address");
        _setupRole(DEFAULT_ADMIN_ROLE, admin);
        _setupRole(CREATOR_ROLE, admin);
        _setupRole(WARDEN_ROLE, admin);
    }

    /**
     * @dev Creates a wrapped token for the specified underlying asset.
     */
    function createToken(
        address _underlying_token,
        string memory name,
        string memory symbol
    ) public onlyRole(CREATOR_ROLE) returns (address) {
        require(_underlying_token != address(0), "Invalid underlying token");
        require(wrapped_tokens[_underlying_token] == address(0), "Token already registered");

        // Deploy new wrapped token
        BridgeToken wrapped_token = new BridgeToken(_underlying_token, name, symbol, address(this));
        address wrapped_token_address = address(wrapped_token);

        // Update mappings
        wrapped_tokens[_underlying_token] = wrapped_token_address;
        underlying_tokens[wrapped_token_address] = _underlying_token;

        // Register the underlying token
        tokens.push(_underlying_token);

        // Emit creation event
        emit Creation(_underlying_token, wrapped_token_address);

        return wrapped_token_address;
    }

    /**
     * @dev Wraps the specified amount of an underlying token.
     */
    function wrap(
        address _underlying_token,
        address _recipient,
        uint256 _amount
    ) public onlyRole(WARDEN_ROLE) {
        require(_underlying_token != address(0), "Invalid underlying token");
        require(_recipient != address(0), "Invalid recipient address");
        require(_amount > 0, "Amount must be greater than zero");

        address wrapped_token = wrapped_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token not registered");

        // Mint wrapped tokens
        BridgeToken(wrapped_token).mint(_recipient, _amount);

        // Emit wrap event
        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);
    }

    /**
     * @dev Unwraps the specified amount of a wrapped token.
     */
    function unwrap(
        address _wrapped_token,
        address _recipient,
        uint256 _amount
    ) public {
        require(_wrapped_token != address(0), "Invalid wrapped token");
        require(_recipient != address(0), "Invalid recipient address");
        require(_amount > 0, "Amount must be greater than zero");

        address underlying_token = underlying_tokens[_wrapped_token];
        require(underlying_token != address(0), "Underlying token not registered");

        // Burn wrapped tokens from sender
        BridgeToken(_wrapped_token).burnFrom(msg.sender, _amount);

        // Emit unwrap event
        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);
    }

    /**
     * @dev Returns the list of all registered underlying tokens.
     */
    function getTokens() external view returns (address[] memory) {
        return tokens;
    }
}
