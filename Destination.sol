// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    using SafeERC20 for ERC20;

    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
    mapping(address => address) public underlying_tokens;
    mapping(address => address) public wrapped_tokens;
    address[] public tokens;

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address indexed frm, uint256 amount);

    constructor(address admin) {
        require(admin != address(0), "Admin address cannot be zero");
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

    function wrap(address _underlying_token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        require(_underlying_token != address(0), "Invalid underlying token address");
        require(_recipient != address(0), "Recipient cannot be zero address");
        require(_amount > 0, "Amount must be greater than zero");
        require(underlying_tokens[_underlying_token] != address(0), "Underlying token not supported");

        address wrapped_token = underlying_tokens[_underlying_token];
        require(wrapped_token != address(0), "Wrapped token not found");

        // Transfer the underlying tokens from the caller to this contract
        ERC20(_underlying_token).safeTransferFrom(msg.sender, address(this), _amount);

        // Mint the wrapped tokens to the recipient
        BridgeToken(wrapped_token).mint(_recipient, _amount);

        emit Wrap(_underlying_token, wrapped_token, _recipient, _amount);
    }

    function unwrap(address _wrapped_token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        require(_wrapped_token != address(0), "Invalid wrapped token address");
        require(_recipient != address(0), "Recipient cannot be zero address");
        require(_amount > 0, "Amount must be greater than zero");
        require(wrapped_tokens[_wrapped_token] != address(0), "Wrapped token not supported");

        address underlying_token = wrapped_tokens[_wrapped_token];
        require(underlying_token != address(0), "Underlying token not found");

        // Burn the wrapped tokens from the caller
        BridgeToken(_wrapped_token).burnFrom(msg.sender, _amount);

        // Transfer the underlying tokens to the recipient
        ERC20(underlying_token).safeTransfer(_recipient, _amount);

        emit Unwrap(underlying_token, _wrapped_token, msg.sender, _amount);
    }

    function createToken(address _underlying_token, string memory name, string memory symbol) 
        public 
        onlyRole(CREATOR_ROLE) 
        returns (address) 
    {
        require(_underlying_token != address(0), "Invalid underlying token address");
        require(underlying_tokens[_underlying_token] == address(0), "Token already exists");

        // Deploy a new BridgeToken
        BridgeToken wrapped_token = new BridgeToken(_underlying_token, name, symbol, address(this));

        // Map the underlying token to the wrapped token
        underlying_tokens[_underlying_token] = address(wrapped_token);
        wrapped_tokens[address(wrapped_token)] = _underlying_token;
        tokens.push(_underlying_token);

        emit Creation(_underlying_token, address(wrapped_token));

        return address(wrapped_token);
    }

    function getTokens() public view returns (address[] memory) {
        return tokens;
    }
}
