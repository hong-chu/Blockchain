// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
    mapping(address => address) public underlying_tokens;
    mapping(address => address) public wrapped_tokens;
    address[] public tokens;

    event Creation(address indexed underlying_token, address indexed wrapped_token);
    event Wrap(address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount);
    event Unwrap(address indexed underlying_token, address indexed wrapped_token, address frm, address indexed to, uint256 amount);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

    function wrap(address _underlying_token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        require(underlying_tokens[_underlying_token] != address(0), "Underlying token not supported");
        require(wrapped_tokens[_underlying_token] != address(0), "Wrapped token not supported");
        require(ERC20(_underlying_token).transferFrom(_recipient, address(this), _amount), "Transfer failed");
        emit Wrap(_underlying_token, wrapped_tokens[_underlying_token], _recipient, _amount);
        ERC20(wrapped_tokens[_underlying_token]).transfer(_recipient, _amount);
    }

    function unwrap(address _wrapped_token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        require(wrapped_tokens[_wrapped_token] != address(0), "Wrapped token not supported");
        require(underlying_tokens[_wrapped_token] != address(0), "Underlying token not supported");
        require(ERC20(_wrapped_token).transferFrom(_recipient, address(this), _amount), "Transfer failed");
        emit Unwrap(_wrapped_token, underlying_tokens[_wrapped_token], msg.sender, _recipient, _amount);
        ERC20(underlying_tokens[_wrapped_token]).transfer(_recipient, _amount);
    }

    function createToken(address _underlying_token, string memory name, string memory symbol) public onlyRole(CREATOR_ROLE) returns(address) {
        address wrapped_token = address(new BridgeToken(_underlying_token, name, symbol, msg.sender));
        underlying_tokens[wrapped_token] = _underlying_token;
        wrapped_tokens[_underlying_token] = wrapped_token;
        tokens.push(_underlying_token);
        emit Creation(_underlying_token, wrapped_token);
        return wrapped_token;
    }
}