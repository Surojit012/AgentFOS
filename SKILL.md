# AgentFOS Pharos Skill

## Prerequisites

- Foundry must be installed and available as `cast` and `forge`.
- Export `PRIVATE_KEY` before write operations.
- Export `RPC=https://atlantic.dplabs-internal.com` for Atlantic Testnet.
- Never hardcode private keys in scripts, docs, or committed files.

## Network Configuration

| Network | RPC | Chain ID | Explorer |
|---------|-----|----------|----------|
| Pharos Atlantic Testnet | `https://atlantic.dplabs-internal.com` | `688689` | `https://atlantic.pharosscan.xyz/` |

## Capability Index

| User Need | Capability | Detailed Instructions |
|-----------|------------|----------------------|
| Deploy AgentFOS skill / deploy the RWA allocation contract | `forge script` AgentFOS deployment | -> `references/agentfos.md#deploy-agentfos-skill-contract` |
| Verify AgentFOS contract / publish source on PharosScan | `forge verify-contract` | -> `references/agentfos.md#verify-agentfos-skill-contract` |
| Generate an on-chain RWA allocation / write AgentFOS result to Pharos | `cast send allocate(string,uint256,uint256)` | -> `references/agentfos.md#generate-allocation` |
| Check protocol risk / read on-chain risk score | `cast call getRiskScore(string)` | -> `references/agentfos.md#get-risk-score` |
| Read latest allocation / inspect last AgentFOS decision | `cast call getLastAllocation()` | -> `references/agentfos.md#get-last-allocation` |
| Check AgentFOS owner / confirm fee withdrawal authority | `cast call owner()` | -> `references/agentfos.md#get-owner` |
| Check allocation fee / confirm required PHRS payment | `cast call ALLOCATION_FEE()` | -> `references/agentfos.md#get-allocation-fee` |
| Query AgentFOS allocation events / show allocation history | `cast logs AllocationGenerated` | -> `references/agentfos.md#query-allocation-events` |
| Withdraw AgentFOS fees / collect earned PHRS | `cast send withdrawFees(address)` | -> `references/agentfos.md#withdraw-fees` |
| Query AgentFOS fee withdrawals / show earned PHRS withdrawals | `cast logs FeeWithdrawn` | -> `references/agentfos.md#query-fee-withdrawal-events` |

## Write Operation Pre-checks

1. Confirm Foundry is installed: `which cast` and `which forge`.
2. Confirm the private key derives the expected wallet: `cast wallet address --private-key $PRIVATE_KEY`.
3. Confirm Atlantic RPC is reachable: `cast chain-id --rpc-url $RPC`.
4. Confirm the wallet has enough PHRS for value plus gas: `cast balance $DEPLOYER --rpc-url $RPC --ether`.

## General Error Handling

| Error | Cause | Suggested Action |
|-------|-------|------------------|
| `cast: command not found` | Foundry is not installed | Install Foundry, then rerun `foundryup` |
| `connection refused` | Missing `--rpc-url`; Foundry used localhost | Always pass `--rpc-url $RPC` |
| `insufficient funds` | Wallet cannot cover fee plus gas | Fund the wallet with Atlantic PHRS |
| `execution reverted` | Contract validation failed | Read the revert reason and correct inputs |

## Security Reminders

- Pass private keys explicitly through `--private-key $PRIVATE_KEY`.
- Do not commit `.env`, `.env.local`, broadcast artifacts containing sensitive data, or private keys.
- Use read-only `cast call` commands before write commands when verifying a deployment.
