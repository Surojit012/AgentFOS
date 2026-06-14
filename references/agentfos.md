# AgentFOS Operation Instructions

> Network: Atlantic RPC is `https://atlantic.dplabs-internal.com`
>
> Private key: pass explicitly via `--private-key $PRIVATE_KEY`
>
> Explorer: `https://atlantic.pharosscan.xyz/`

---

## Deploy AgentFOS Skill Contract

### Overview

Deploy the payable AgentFOS Skill contract that stores protocol risk scores and the latest allocation on Pharos Atlantic Testnet.

### Command Template

```bash
forge build
forge script script/DeployAgentFOS.s.sol:DeployAgentFOS \
  --rpc-url $RPC \
  --private-key $PRIVATE_KEY \
  --broadcast
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |
| `PRIVATE_KEY` | hex string | Yes | Deployer wallet private key. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `Contract Address` | Save this as `AGENTFOS_CONTRACT_ADDRESS` for backend and read commands. |
| `Transaction Hash` | Use this hash to inspect the deployment on PharosScan. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| `forge: command not found` | Foundry is not installed | Install Foundry and run `foundryup`. |
| `insufficient funds` | Deployer lacks PHRS for gas | Fund the deployer wallet on Atlantic. |
| `connection refused` | Missing or incorrect RPC URL | Export `RPC=https://atlantic.dplabs-internal.com`. |

> **Agent Guidelines**
>
> 1. Complete the write-operation pre-checks from `SKILL.md`.
> 2. Run `forge build` before broadcasting.
> 3. Capture the contract address and update `AGENTFOS_CONTRACT_ADDRESS`.

---

## Verify AgentFOS Skill Contract

### Overview

Verify the deployed source on the Pharos Atlantic Blockscout-compatible explorer.

### Command Template

```bash
sleep 10
forge verify-contract <contract_address> src/AgentFOSSkill.sol:AgentFOSSkill \
  --chain-id 688689 \
  --verifier-url https://api.socialscan.io/pharos-atlantic-testnet/v1/explorer/command_api/contract \
  --verifier blockscout
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `contract_address` | address | Yes | Deployed `AgentFOSSkill` contract address. |
| `chain-id` | uint256 | Yes | Pharos Atlantic chain ID: `688689`. |

### Output Parsing

| Field | Description |
|-------|-------------|
| Verification response | Success means the source should become visible on PharosScan after indexing. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| `psycopg2` / SQL error | Explorer indexer is not ready | Wait at least 10 seconds and retry. |
| `Contract source code already verified` | Verification already succeeded | Treat as success. |
| `Invalid chain id` | Wrong chain ID | Use `--chain-id 688689`. |

> **Agent Guidelines**
>
> 1. Wait 10 seconds after deployment before verifying.
> 2. Use the exact source path `src/AgentFOSSkill.sol:AgentFOSSkill`.
> 3. Return the PharosScan contract URL to the user.

---

## Generate Allocation

### Overview

Write an AgentFOS allocation decision on-chain. The call charges exactly `0.001 PHRS`, stores the protocol risk score, stores the latest allocation tuple, and emits `AllocationGenerated`.

### Command Template

```bash
cast send $AGENTFOS_CONTRACT_ADDRESS \
  "allocate(string,uint256,uint256)" \
  <protocol> <risk_score> <apy_bps> \
  --value 0.001ether \
  --private-key $PRIVATE_KEY \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `protocol` | string | Yes | Protocol key such as `ondo`, `zoth`, `maple`, `centrifuge`, `backed`, or `opentrade`. |
| `risk_score` | uint256 | Yes | Deterministic score from `0` to `100`. |
| `apy_bps` | uint256 | Yes | APY in basis points, e.g. `470` for `4.70%`. |
| `PRIVATE_KEY` | hex string | Yes | Sender private key. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `transactionHash` | On-chain transaction hash for the allocation. |
| `blockNumber` | Block containing the allocation if included in output. |
| `status` | A successful receipt means the allocation is stored. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| `AgentFOS: fee must be 0.001 PHRS` | Wrong `--value` | Use `--value 0.001ether`. |
| `AgentFOS: protocol required` | Empty protocol string | Pass a supported protocol key. |
| `AgentFOS: risk score exceeds 100` | Invalid risk score | Recompute deterministic risk score and retry. |
| `insufficient funds` | Wallet lacks PHRS | Fund wallet for fee plus gas. |

> **Agent Guidelines**
>
> 1. Complete the write-operation pre-checks from `SKILL.md`.
> 2. Convert APY percent to basis points before calling, for example `round(4.7 * 100) = 470`.
> 3. After success, run `getLastAllocation()` to confirm stored state.

---

## Get Risk Score

### Overview

Read the latest stored on-chain risk score for a protocol.

### Command Template

```bash
cast call $AGENTFOS_CONTRACT_ADDRESS \
  "getRiskScore(string)(uint256)" \
  <protocol> \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `protocol` | string | Yes | Protocol key to query. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `uint256` | Risk score from `0` to `100`; `0` can mean no score has been written yet. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| Empty return value | No contract code at address | Confirm contract address and network. |
| `invalid address` | Bad contract address | Use a valid `0x` address. |

> **Agent Guidelines**
>
> 1. Use `cast call`; this operation is free and requires no private key.
> 2. If score is `0`, check allocation events before treating the protocol as high risk.

---

## Get Last Allocation

### Overview

Read the latest allocation written by AgentFOS.

### Command Template

```bash
cast call $AGENTFOS_CONTRACT_ADDRESS \
  "getLastAllocation()(address,string,uint256,uint256,uint256)" \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `caller` | Wallet that submitted the latest allocation. |
| `protocol` | Protocol key stored in the latest allocation. |
| `riskScore` | Stored deterministic risk score. |
| `apyBps` | APY in basis points. |
| `timestamp` | Unix timestamp of the allocation transaction block. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| Empty return value | Wrong address or network | Confirm `AGENTFOS_CONTRACT_ADDRESS` and `RPC`. |
| Zero address caller | No allocation has been written yet | Generate an allocation first. |

> **Agent Guidelines**
>
> 1. Use this after `allocate()` to confirm the top protocol and score.
> 2. Convert `apyBps` back to percent by dividing by `100`.

---

## Query Allocation Events

### Overview

Query `AllocationGenerated` events to build an on-chain history of AgentFOS decisions.

### Command Template

```bash
cast logs \
  --from-block 0 \
  --address $AGENTFOS_CONTRACT_ADDRESS \
  "AllocationGenerated(address,string,uint256,uint256)" \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from-block` | uint256 | Yes | Starting block for event scan. Use deployment block when known. |
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `caller` | Indexed caller address that generated the allocation. |
| `protocol` | Protocol string emitted by the contract. |
| `riskScore` | Risk score emitted with the allocation. |
| `timestamp` | Block timestamp emitted by the contract. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| No logs returned | No matching events or wrong block range | Start from deployment block or `0`. |
| `invalid topic` | Event signature typo | Use the exact signature in the command template. |

> **Agent Guidelines**
>
> 1. Prefer the deployment block over `0` when known to reduce RPC load.
> 2. Link transaction hashes to `https://atlantic.pharosscan.xyz/`.

---

## Get Owner

### Overview

Read the AgentFOS contract owner. Only this address can withdraw accumulated PHRS fees.

### Command Template

```bash
cast call $AGENTFOS_CONTRACT_ADDRESS \
  "owner()(address)" \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `address` | Owner wallet that can call `withdrawFees(address)`. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| Empty return value | Wrong address or network | Confirm contract address and `RPC`. |
| `invalid address` | Bad contract address | Use a valid `0x` address. |

> **Agent Guidelines**
>
> 1. Use this before fee withdrawal.
> 2. Compare the returned owner with `cast wallet address --private-key $PRIVATE_KEY`.

---

## Get Allocation Fee

### Overview

Read the exact fee required by `allocate(string,uint256,uint256)`.

### Command Template

```bash
cast call $AGENTFOS_CONTRACT_ADDRESS \
  "ALLOCATION_FEE()(uint256)" \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `uint256` | Fee in wei. `1000000000000000` equals `0.001 PHRS`. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| Empty return value | Wrong address or network | Confirm contract address and `RPC`. |
| `invalid address` | Bad contract address | Use a valid `0x` address. |

> **Agent Guidelines**
>
> 1. Use this to confirm the required `--value`.
> 2. Pass `--value 0.001ether` when generating allocations.

---

## Withdraw Fees

### Overview

Withdraw accumulated `0.001 PHRS` allocation fees from the AgentFOS contract. Only the deployer owner can call this.

### Command Template

```bash
cast send $AGENTFOS_CONTRACT_ADDRESS \
  "withdrawFees(address)" \
  <recipient> \
  --private-key $PRIVATE_KEY \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `recipient` | address | Yes | Wallet that receives accumulated PHRS fees. |
| `PRIVATE_KEY` | hex string | Yes | Owner private key. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `transactionHash` | Transaction hash for the withdrawal. |
| `status` | A successful receipt means fees were transferred. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| `AgentFOS: caller is not owner` | Non-owner private key used | Use the deployer owner key. |
| `AgentFOS: recipient required` | Recipient is zero address | Pass a real payable wallet address. |
| `AgentFOS: no fees to withdraw` | Contract balance is zero | Wait for allocation fees to accrue. |
| `AgentFOS: withdrawal failed` | Recipient transfer failed | Try another payable recipient address. |

> **Agent Guidelines**
>
> 1. Confirm the owner wallet before calling.
> 2. Query contract balance before withdrawal with `cast balance $AGENTFOS_CONTRACT_ADDRESS --rpc-url $RPC --ether`.
> 3. Return the transaction hash and updated contract balance.

---

## Query Fee Withdrawal Events

### Overview

Query `FeeWithdrawn` events to show where AgentFOS revenue was withdrawn.

### Command Template

```bash
cast logs \
  --from-block 0 \
  --address $AGENTFOS_CONTRACT_ADDRESS \
  "FeeWithdrawn(address,uint256)" \
  --rpc-url $RPC
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from-block` | uint256 | Yes | Starting block for event scan. Use deployment block when known. |
| `AGENTFOS_CONTRACT_ADDRESS` | address | Yes | Deployed AgentFOS contract. |
| `RPC` | URL | Yes | Pharos Atlantic RPC URL. |

### Output Parsing

| Field | Description |
|-------|-------------|
| `recipient` | Indexed recipient address that received withdrawn PHRS. |
| `amount` | Withdrawn amount in wei. Divide by `1e18` for PHRS. |

### Error Handling

| Error Signature | Cause | Suggested Action |
|----------------|-------|------------------|
| No logs returned | No withdrawals or wrong block range | Start from deployment block or `0`. |
| `invalid topic` | Event signature typo | Use the exact signature in the command template. |

> **Agent Guidelines**
>
> 1. Prefer the deployment block over `0` when known.
> 2. Convert `amount` from wei to PHRS before presenting it.
