// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract AgentFOSSkill {
    uint256 public constant ALLOCATION_FEE = 0.001 ether;

    address private immutable OWNER;

    struct Allocation {
        address caller;
        string protocol;
        uint256 riskScore;
        uint256 apyBps;
        uint256 timestamp;
    }

    mapping(string protocol => uint256 riskScore) private riskScores;
    Allocation private lastAllocation;

    event AllocationGenerated(
        address indexed caller,
        string protocol,
        uint256 riskScore,
        uint256 timestamp
    );
    event FeeWithdrawn(address indexed recipient, uint256 amount);

    constructor() {
        OWNER = msg.sender;
    }

    function owner() external view returns (address) {
        return OWNER;
    }

    function allocate(
        string calldata protocol,
        uint256 riskScore,
        uint256 apyBps
    ) external payable {
        require(msg.value == ALLOCATION_FEE, "AgentFOS: fee must be 0.001 PHRS");
        require(bytes(protocol).length > 0, "AgentFOS: protocol required");
        require(riskScore <= 100, "AgentFOS: risk score exceeds 100");

        riskScores[protocol] = riskScore;
        lastAllocation = Allocation({
            caller: msg.sender,
            protocol: protocol,
            riskScore: riskScore,
            apyBps: apyBps,
            timestamp: block.timestamp
        });

        emit AllocationGenerated(msg.sender, protocol, riskScore, block.timestamp);
    }

    function getRiskScore(string calldata protocol) external view returns (uint256) {
        return riskScores[protocol];
    }

    function getLastAllocation()
        external
        view
        returns (
            address caller,
            string memory protocol,
            uint256 riskScore,
            uint256 apyBps,
            uint256 timestamp
        )
    {
        Allocation memory allocation = lastAllocation;
        return (
            allocation.caller,
            allocation.protocol,
            allocation.riskScore,
            allocation.apyBps,
            allocation.timestamp
        );
    }

    function withdrawFees(address payable recipient) external {
        require(msg.sender == OWNER, "AgentFOS: caller is not owner");
        require(recipient != address(0), "AgentFOS: recipient required");

        uint256 amount = address(this).balance;
        require(amount > 0, "AgentFOS: no fees to withdraw");

        (bool sent, ) = recipient.call{value: amount}("");
        require(sent, "AgentFOS: withdrawal failed");

        emit FeeWithdrawn(recipient, amount);
    }
}
