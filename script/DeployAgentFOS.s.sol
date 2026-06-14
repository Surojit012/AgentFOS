// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentFOSSkill} from "../src/AgentFOSSkill.sol";

interface Vm {
    function startBroadcast() external;
    function stopBroadcast() external;
}

contract DeployAgentFOS {
    Vm private constant VM = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    function run() external returns (AgentFOSSkill skill) {
        VM.startBroadcast();
        skill = new AgentFOSSkill();
        VM.stopBroadcast();
    }
}
