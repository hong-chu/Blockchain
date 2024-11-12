// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");

    mapping(address => address) public wrapped_tokens; // Mapping from underlying to wrapped tokens
    mapping(address => address) public underlying_tokens; // Mapping from wrapped to underlying tokens
    address[] public tokens; // List of registered tokens

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address indexed from, address to, uint256 amount);

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
        require(wrapped_tokens[_underlying_token] == address(0), "Token already exists");

        // Deploy the wrapped token
        BridgeToken wrapped_token = new BridgeToken(_underlying_token, name, symbol, address(this));

        // Map underlying to wrapped and vice versa
        wrapped_tokens[_underlying_token] = address(wrapped_token);
        underlying_tokens[address(wrapped_token)] = _underlying_token;

        // Add to registered tokens
        tokens.push(_underlying_token);

        // Emit the creation event
        emit Creation(_underlying_token, address(wrapped_token));

        return address(wrapped_token);
    }

    /**
     * @dev Wraps the specified amount of an underlying token into its wrapped counterpart.
     */
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
        require(wrapped_token != address(0), "Wrapped token not found");
    
        // Mint the correct amount of the wrapped token to the recipient
        BridgeToken(wrapped_token).mint(_recipient, _amount);
    
        // Emit the Wrap event with correct argument order
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
        require(_recipient != address(0), "Recipient cannot be zero");
        require(_amount > 0, "Amount must be greater than zero");

        // Fetch underlying token
        address underlying_token = underlying_tokens[_wrapped_token];
        require(underlying_token != address(0), "Underlying token does not exist");

        // Verify the sender has sufficient balance
        BridgeToken token = BridgeToken(_wrapped_token);
        require(token.balanceOf(msg.sender) >= _amount, "Insufficient balance");

        // Burn the tokens from the sender
        token.burnFrom(msg.sender, _amount);

        // Emit the unwrap event
        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);
    }
}
