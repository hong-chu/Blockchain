pragma solidity ^0.8.17;

import "forge-std/Test.sol";
import "../src/Attacker.sol";
import "../src/Bank.sol";
import "@openzeppelin/contracts/utils/introspection/ERC1820Registry.sol";

contract AttackerTest is Test {
    Attacker attacker;
    Bank bank;
    ERC1820Registry erc1820;

    address attackerAdmin = address(1);

    function setUp() public {
        // Deploy the ERC1820 registry
        erc1820 = new ERC1820Registry();

        // Set the ERC1820 registry code at the expected address
        vm.etch(
            address(0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24),
            address(erc1820).code
        );

        // Deploy the Bank contract
        bank = new Bank(address(this));

        // Deploy the Attacker contract with the correct arguments
        attacker = new Attacker(attackerAdmin, address(0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24));

        // Set the target bank in the attacker contract
        vm.prank(attackerAdmin);
        attacker.setTarget(address(bank));
    }

    function testAttack() public {
        vm.deal(attackerAdmin, 1 ether);

        vm.startPrank(attackerAdmin);

        // Execute the attack
        attacker.attack{value: 1 ether}(1 ether);

        vm.stopPrank();

        // Assert the attacker's token balance has increased
        ERC777 token = bank.token();
        uint256 attackerTokenBalance = token.balanceOf(address(attacker));

        // The balance should be greater than the initial deposit amount due to the reentrancy attack
        assert(attackerTokenBalance > 1 ether);
    }
}
