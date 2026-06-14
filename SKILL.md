# AgentFOS Pharos Skill

AgentFOS is a Pharos-native financial decision skill.

It exposes a small set of commands for deployment, verification, read-only inspection, paid allocation writes, and fee recovery. The goal is simple: make the decision pipeline readable, writable, and provable on Atlantic Testnet.

## Prerequisites

- Foundry must be installed and available as `cast` and `forge`
- Export `PRIVATE_KEY` before any write operation
- Export `RPC=https://atlantic.dplabs-internal.com` for Atlantic Testnet
- Never hardcode private keys in scripts, docs, or committed files

## Network Configuration

| Network | RPC | Chain ID | Explorer |
|---------|-----|----------|----------|
| Pharos Atlantic Testnet | `https://atlantic.dplabs-internal.com` | `688689` | `https://atlantic.pharosscan.xyz/` |

## Capability Index

| User Need | Command Pattern | Read More |
|-----------|-----------------|-----------|
| Deploy the AgentFOS Skill contract | `forge build` + `forge script script/DeployAgentFOS.s.sol:DeployAgentFOS --rpc-url $RPC --private-key $PRIVATE_KEY --broadcast` | [Deploy flow](references/agentfos.md#deploy-agentfos-skill-contract) |
| Verify the contract on PharosScan | `forge verify-contract` | [Verification flow](references/agentfos.md#verify-agentfos-skill-contract) |
| Write a paid allocation on-chain | `cast send ... "allocate(string,uint256,uint256)" ... --value 0.001ether` | [Allocation write](references/agentfos.md#generate-allocation) |
| Read a stored protocol risk score | `cast call ... "getRiskScore(string)(uint256)"` | [Risk score read](references/agentfos.md#get-risk-score) |
| Read the latest stored allocation | `cast call ... "getLastAllocation()(address,string,uint256,uint256,uint256)"` | [Latest allocation](references/agentfos.md#get-last-allocation) |
| Check who owns the contract | `cast call ... "owner()(address)"` | [Owner read](references/agentfos.md#get-owner) |
| Check the exact allocation fee | `cast call ... "ALLOCATION_FEE()(uint256)"` | [Fee read](references/agentfos.md#get-allocation-fee) |
| Inspect allocation history | `cast logs ... "AllocationGenerated(address,string,uint256,uint256)"` | [Event history](references/agentfos.md#query-allocation-events) |
| Withdraw contract fees | `cast send ... "withdrawFees(address)" ...` | [Fee withdrawal](references/agentfos.md#withdraw-fees) |
| Inspect fee withdrawal history | `cast logs ... "FeeWithdrawn(address,uint256)"` | [Withdrawal events](references/agentfos.md#query-fee-withdrawal-events) |

## Write Operation Pre-checks

Before any command that changes contract state:

1. Confirm Foundry is installed: `which cast` and `which forge`
2. Confirm the private key derives the expected wallet: `cast wallet address --private-key $PRIVATE_KEY`
3. Confirm Atlantic RPC is reachable: `cast chain-id --rpc-url $RPC`
4. Confirm the wallet has enough PHRS for fee plus gas: `cast balance $DEPLOYER --rpc-url $RPC --ether`

## General Error Handling

| Error | Cause | Suggested Action |
|-------|-------|------------------|
| `cast: command not found` | Foundry is not installed | Install Foundry, then run `foundryup` |
| `connection refused` | Missing or incorrect RPC URL | Export `RPC=https://atlantic.dplabs-internal.com` |
| `insufficient funds` | Wallet cannot cover fee plus gas | Fund the wallet with Atlantic PHRS |
| `execution reverted` | Contract validation failed | Read the revert reason and correct inputs |

## Security Reminders

- Pass private keys explicitly through `--private-key $PRIVATE_KEY`
- Do not commit `.env`, `.env.local`, broadcast artifacts, or private keys
- Use read-only `cast call` commands before any write command when verifying a deployment
- When presenting results to a judge, include the transaction hash and the PharosScan link
