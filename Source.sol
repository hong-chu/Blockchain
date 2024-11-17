// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol"; // Ensure this import is correct

contract Source is AccessControl {
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");

    mapping(address => bool) public approved;
    address[] public tokens;

    // Mapping from underlying token to its corresponding BridgeToken
    mapping(address => BridgeToken) public bridgeTokens;

    event Deposit(address indexed token, address indexed recipient, uint256 amount);
    event Withdrawal(address indexed token, address indexed recipient, uint256 amount);
    event Registration(address indexed token);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ADMIN_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

    /*
        Allows users to deposit approved tokens.
        Transfers the underlying tokens to the contract and mints BridgeTokens to the depositor.
    */
    function deposit(address _token, address _recipient, uint256 _amount) public {
        require(approved[_token], "Token not approved");
        require(_amount > 0, "Amount must be greater than zero");
        require(_recipient != address(0), "Invalid recipient address");

        // Transfer underlying tokens from sender to this contract
        ERC20(_token).transferFrom(msg.sender, address(this), _amount);

        // Mint BridgeTokens to the depositor (msg.sender)
        BridgeToken bridgeToken = bridgeTokens[_token];
        bridgeToken.mint(msg.sender, _amount);

        // Emit the Deposit event with the provided _recipient
        emit Deposit(_token, _recipient, _amount);
    }

    /*
        Allows the WARDEN_ROLE to withdraw tokens on behalf of a recipient.
        Burns the recipient's BridgeTokens and transfers the underlying tokens to them.
    */
    function withdraw(address _token, address _recipient, uint256 _amount) public onlyRole(WARDEN_ROLE) {
        require(approved[_token], "Token not approved");
        require(_amount > 0, "Amount must be greater than zero");
        require(_recipient != address(0), "Invalid recipient address");

        // Burn BridgeTokens from the _recipient
        BridgeToken bridgeToken = bridgeTokens[_token];
        bridgeToken.burnFrom(_recipient, _amount);

        // Transfer underlying tokens from this contract to the _recipient
        ERC20(_token).transfer(_recipient, _amount);

        emit Withdrawal(_token, _recipient, _amount);
    }

    /*
        Registers a new token to the bridge.
        Only callable by an address with the ADMIN_ROLE.
    */
    function registerToken(address _token) public onlyRole(ADMIN_ROLE) {
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
