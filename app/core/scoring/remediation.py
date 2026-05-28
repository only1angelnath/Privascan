"""
Remediation recommendations mapped from Slither check names.
Rule-based, deterministic — no ML. Runs at query time.
"""

REMEDIATION_MAP: dict[str, str] = {
    # Reentrancy
    "reentrancy-eth": "Add ReentrancyGuard modifier from OpenZeppelin to all withdraw functions",
    "reentrancy-no-eth": "Apply checks-effects-interactions pattern or add ReentrancyGuard",
    "reentrancy-benign": "Review function order; apply checks-effects-interactions pattern",
    "reentrancy-events": "Emit events after all state changes, not before",

    # Access control
    "unprotected-upgrade": "Add onlyOwner or onlyRole access control to upgrade function",
    "suicidal": "Remove selfdestruct or add strict multi-sig access control",
    "arbitrary-send-eth": "Validate recipient address before sending ETH; use pull-payment pattern",
    "controlled-delegatecall": "Remove delegatecall or strictly whitelist call targets",
    "tx-origin": "Replace tx.origin with msg.sender for all authentication checks",
    "msg-value-loop": "Never use msg.value inside a loop; cache value before loop entry",

    # Arithmetic
    "divide-before-multiply": "Reorder operations: multiply before divide to preserve precision",
    "tautology": "Remove redundant condition; review logic for off-by-one errors",
    "boolean-equality": "Compare booleans directly (if flag) not (if flag == true)",

    # Variables
    "uninitialized-local": "Initialize all local variables before use",
    "uninitialized-state": "Initialize all state variables in constructor",
    "shadowing-state": "Rename local variable to avoid shadowing state variable",
    "shadowing-abstract": "Rename to avoid shadowing inherited abstract variable",
    "constable-variables": "Mark variable as constant to save gas and prevent mutation",
    "immutable-states": "Mark variable as immutable if set only in constructor",

    # Low-level calls
    "low-level-calls": "Replace low-level call() with named function calls where possible",
    "unchecked-lowlevel": "Always check return value of low-level call()",
    "unchecked-send": "Check return value of send(); prefer transfer() or call()",
    "unchecked-transfer": "Check return value of ERC20 transfer(); use SafeERC20",

    # Locks / logic
    "locked-ether": "Add a withdraw function so ETH sent to contract can be recovered",
    "calls-loop": "Avoid external calls inside loops; use pull-payment pattern",
    "incorrect-equality": "Use >= or <= instead of strict equality for ETH/token balance checks",
    "weak-prng": "Replace block.timestamp / blockhash randomness with Chainlink VRF",

    # Privacy-specific
    "mixer-reentrancy": "Add ReentrancyGuard to pool withdraw; audit note/shield balance update order",
    "zk-verifier-bypass": "Harden verifier: add circuit-level range checks and input validation",
    "relayer-fee-manipulation": "Validate fee parameters on-chain; cap maximum relayer fee percentage",
    "fhe-decryption-acl-bypass": "Audit ACL contract; add multi-sig to ACL admin role",
    "fhe-handle-leak": "Audit handle lifecycle; ensure handles are invalidated after use",
}

def get_remediation(check: str) -> str:
    """Return remediation text for a Slither check name, or a generic fallback."""
    return REMEDIATION_MAP.get(
        check,
        f"Review the {check} finding manually and apply appropriate mitigation"
    )
