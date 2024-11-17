// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract Source is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
	mapping( address => bool) public approved;
	address[] public tokens;

	event Deposit( address indexed token, address indexed recipient, uint256 amount );
	event Withdrawal( address indexed token, address indexed recipient, uint256 amount );
	event Registration( address indexed token );

    constructor( address admin ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);

    }

	function deposit(address _token, address _recipient, uint256 _amount ) public {
		//YOUR CODE HERE
    require(approved[_token], "Token not approved");
    require(_amount > 0, "Amount must be greater than zero");
    require(_recipient != address(0), "Invalid recipient address");

    // Transfer underlying tokens from sender to this contract
    ERC20(_token).transferFrom(msg.sender, address(this), _amount);

    // Mint BridgeTokens to the recipient
    BridgeToken bridgeToken = bridgeTokens[_token];
    bridgeToken.mint(_recipient, _amount);

    emit Deposit(_token, _recipient, _amount);
	}

	function withdraw(address _token, address _recipient, uint256 _amount ) onlyRole(WARDEN_ROLE) public {
		//YOUR CODE HERE
    require(approved[_token], "Token not approved");
    require(_amount > 0, "Amount must be greater than zero");
    require(_recipient != address(0), "Invalid recipient address");

    // Burn BridgeTokens from the recipient
    BridgeToken bridgeToken = bridgeTokens[_token];
    bridgeToken.burnFrom(_recipient, _amount);

    // Transfer underlying tokens from this contract to the recipient
    ERC20(_token).transfer(_recipient, _amount);

    emit Withdrawal(_token, _recipient, _amount);
	}

	function registerToken(address _token) onlyRole(ADMIN_ROLE) public {
		//YOUR CODE HERE
    require(!approved[_token], "Token already registered");
    require(_token != address(0), "Invalid token address");

    approved[_token] = true;
    tokens.push(_token);

    // Create a new BridgeToken for the underlying token
    string memory name = string(abi.encodePacked("Bridge ", ERC20(_token).name()));
    string memory symbol = string(abi.encodePacked("b", ERC20(_token).symbol()));

    BridgeToken bridgeToken = new BridgeToken(_token, name, symbol, address(this));

    bridgeTokens[_token] = bridgeToken;

    emit Registration(_token);
	}


}


