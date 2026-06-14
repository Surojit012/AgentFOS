"""
Pharos on-chain writer for AgentFOS allocation records.

Keeps the backend demo-safe: allocation responses still succeed if the
contract is not configured, Foundry is unavailable, or the RPC call fails.
"""

import re
import subprocess
from dataclasses import dataclass
from typing import Optional

from config import settings
from models.schemas import AllocationItem


@dataclass(frozen=True)
class OnchainWriteResult:
    status: str
    tx_hash: Optional[str] = None
    error: Optional[str] = None


def record_allocation_onchain(allocation: AllocationItem) -> OnchainWriteResult:
    """Write the top AgentFOS allocation to Pharos through cast send."""
    if not settings.AGENTFOS_CONTRACT_ADDRESS:
        return OnchainWriteResult(
            status="skipped",
            error="AGENTFOS_CONTRACT_ADDRESS is not configured.",
        )
    if not settings.PHAROS_PRIVATE_KEY:
        return OnchainWriteResult(
            status="skipped",
            error="PHAROS_PRIVATE_KEY is not configured.",
        )

    apy_bps = round(allocation.apy * 100)
    command = [
        "cast",
        "send",
        settings.AGENTFOS_CONTRACT_ADDRESS,
        "allocate(string,uint256,uint256)",
        allocation.protocol_key,
        str(allocation.risk_score),
        str(apy_bps),
        "--value",
        "0.001ether",
        "--private-key",
        settings.PHAROS_PRIVATE_KEY,
        "--rpc-url",
        settings.PHAROS_RPC_URL,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        return OnchainWriteResult(status="failed", error="cast command not found.")
    except subprocess.TimeoutExpired:
        return OnchainWriteResult(status="failed", error="cast send timed out.")
    except Exception as exc:
        return OnchainWriteResult(status="failed", error=str(exc))

    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if result.returncode != 0:
        return OnchainWriteResult(
            status="failed",
            error=output or f"cast send exited with code {result.returncode}.",
        )

    tx_hash = _extract_tx_hash(output)
    if not tx_hash:
        return OnchainWriteResult(
            status="failed",
            error="cast send succeeded but no transactionHash was found in the receipt.",
        )

    return OnchainWriteResult(status="success", tx_hash=tx_hash)


def _extract_tx_hash(output: str) -> Optional[str]:
    for pattern in (
        r"transactionHash\s+((?:0x)?[a-fA-F0-9]{64})",
        r'"transactionHash"\s*:\s*"((?:0x)?[a-fA-F0-9]{64})"',
        r"\bhash\s+((?:0x)?[a-fA-F0-9]{64})",
    ):
        match = re.search(pattern, output)
        if match:
            tx_hash = match.group(1)
            return tx_hash if tx_hash.startswith("0x") else f"0x{tx_hash}"

    match = re.search(r"0x[a-fA-F0-9]{64}", output)
    return match.group(0) if match else None
