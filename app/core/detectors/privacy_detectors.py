"""
Privacy-specific vulnerability detectors.
These run on raw Solidity source code using pattern matching.
They complement Slither's built-in detectors with privacy protocol context.
"""

import re
import structlog
from app.core.models.scoring import SlitherFinding

log = structlog.get_logger()


def run_all_privacy_detectors(source_code: str, contract_name: str) -> list[SlitherFinding]:
    """
    Run all 5 privacy detectors against raw Solidity source.
    Returns a combined list of findings.
    """
    if not source_code:
        return []

    findings = []
    detectors = [
        detect_mixer_reentrancy,
        detect_zk_verifier_bypass,
        detect_nullifier_reuse,
        detect_admin_key_risk,
        detect_upgrade_no_timelock,
    ]

    for detector in detectors:
        try:
            result = detector(source_code, contract_name)
            findings.extend(result)
        except Exception as e:
            log.warning("privacy_detector.failed", detector=detector.__name__, error=str(e))

    log.info(
        "privacy_detectors.complete",
        contract=contract_name,
        findings=len(findings),
    )
    return findings


def detect_mixer_reentrancy(source_code: str, contract_name: str) -> list[SlitherFinding]:
    """
    Detects reentrancy risk in withdrawal functions specific to mixer patterns.
    Looks for external calls that appear BEFORE nullifier state updates
    in the same function body. The nullifier regex uses \\w* to match
    any variable name starting with 'nullifier' e.g. nullifierHashes,
    nullifierHash, nullifiers — all common naming patterns.
    Amplifier 1.5x because exploiting this drains the entire pool.
    """
    findings = []

    func_bodies = _extract_function_bodies(
        source_code,
        ["withdraw", "transfer", "exit", "dequeue"]
    )

    # Matches .call{ .call( .transfer( .send( with optional whitespace
    external_call_re = re.compile(
        r'\.(call\s*[\{\(]|transfer\s*\(|send\s*\()'
    )
    # Matches nullifierHashes[x] = true, nullifiers[x] = true, etc.
    nullifier_update_re = re.compile(
        r'(nullifier\w*)\s*\[.+?\]\s*=\s*true',
        re.DOTALL
    )

    for func_name, func_body in func_bodies:
        call_match = external_call_re.search(func_body)
        nullifier_match = nullifier_update_re.search(func_body)

        if call_match and nullifier_match:
            if nullifier_match.start() > call_match.start():
                findings.append(SlitherFinding(
                    check="mixer-reentrancy",
                    impact="High",
                    confidence="Medium",
                    description=(
                        f"Function `{func_name}` updates nullifier/commitment state "
                        f"AFTER an external call. An attacker may re-enter before the "
                        f"nullifier is marked as spent, enabling double-withdrawal."
                    ),
                    is_custom=True,
                    amplifier=1.5,
                ))

    return findings


def detect_zk_verifier_bypass(source_code: str, contract_name: str) -> list[SlitherFinding]:
    """
    Detects patterns where ZK proof verification can be bypassed.
    Pattern 1: verifier.verifyProof() call on its own line ending with
               semicolon — return value completely ignored so any proof passes.
    Pattern 2: setter function lets admin replace the verifier contract
               address — compromised admin could swap in a fake verifier.
    Amplifier 2.0x for unchecked result, 1.8x for replaceable verifier.
    """
    findings = []

    # Standalone verify call — not preceded by = or bool assignment
    verify_standalone = re.compile(
        r'(?<![=\w])\s*[\w.]+\.(verify|verifyProof)\s*\([^;]*\)\s*;',
        re.MULTILINE
    )
    for match in verify_standalone.finditer(source_code):
        start = max(0, match.start() - 150)
        before = source_code[start:match.start()]
        if not re.search(r'(=\s*$|require\s*\($|bool\s+\w+\s*$)', before.strip()):
            findings.append(SlitherFinding(
                check="zk-verifier-bypass",
                impact="High",
                confidence="Medium",
                description=(
                    "ZK proof verification result is not checked. The verifier call "
                    "return value is unused — any proof passes as valid regardless "
                    "of correctness."
                ),
                is_custom=True,
                amplifier=2.0,
            ))
            break

    if re.search(r'function\s+set\w*[Vv]erifier\s*\(', source_code, re.IGNORECASE):
        findings.append(SlitherFinding(
            check="zk-verifier-bypass",
            impact="Medium",
            confidence="High",
            description=(
                "Admin can replace the ZK verifier contract via a setter function. "
                "A malicious or compromised admin could swap in a verifier that "
                "accepts any proof, breaking all privacy guarantees."
            ),
            is_custom=True,
            amplifier=1.8,
        ))

    return findings


def detect_nullifier_reuse(source_code: str, contract_name: str) -> list[SlitherFinding]:
    """
    Detects missing nullifier uniqueness checks in withdrawal functions.
    Uses \\w* to match any nullifier variable name variant.
    Amplifier 1.8x — directly enables theft of deposited funds.
    """
    findings = []

    has_nullifier = bool(re.search(
        r'nullifier',
        source_code, re.IGNORECASE
    ))
    if not has_nullifier:
        return findings

    func_bodies = _extract_function_bodies(source_code, ["withdraw", "exit", "claim"])

    for func_name, func_body in func_bodies:
        if not re.search(r'nullifier', func_body, re.IGNORECASE):
            continue

        has_nullifier_check = bool(re.search(
            r'require\s*\(\s*!?\s*(nullifier|spent|used)',
            func_body, re.IGNORECASE
        ))

        if not has_nullifier_check:
            findings.append(SlitherFinding(
                check="nullifier-reuse",
                impact="High",
                confidence="Low",
                description=(
                    f"Function `{func_name}` does not appear to verify nullifier "
                    f"uniqueness before processing withdrawal. Missing nullifier checks "
                    f"enable double-spend attacks."
                ),
                is_custom=True,
                amplifier=1.8,
            ))

    return findings


def detect_admin_key_risk(source_code: str, contract_name: str) -> list[SlitherFinding]:
    """
    Detects dangerous admin capabilities without timelock protection.
    Scans entire source for privileged function declarations using word
    boundaries so 'pause' matches but 'unpause' does not.
    Each dangerous function found without a timelock gets its own finding.
    Amplifier 1.3x — centralisation risk rather than direct exploit.
    """
    findings = []

    has_timelock = bool(re.search(
        r'TimelockController|ITimelock|MINIMUM_DELAY|scheduleBatch',
        source_code, re.IGNORECASE
    ))

    dangerous = [
        (r'function\s+pause\b', "pause the contract"),
        (r'function\s+blacklist\b', "blacklist user addresses"),
        (r'function\s+ban\b', "ban user addresses"),
        (r'function\s+drain\b', "drain contract funds"),
        (r'function\s+emergencyWithdraw\b', "emergency withdraw funds"),
        (r'function\s+sweep\b', "sweep contract funds"),
        (r'function\s+setFee\b', "change protocol fees"),
    ]

    for pattern, description in dangerous:
        if re.search(pattern, source_code, re.IGNORECASE) and not has_timelock:
            findings.append(SlitherFinding(
                check="admin-key-risk",
                impact="Medium",
                confidence="High",
                description=(
                    f"Admin can {description} without timelock protection. "
                    f"A compromised or malicious admin key can immediately affect "
                    f"all users with no on-chain delay for users to exit."
                ),
                is_custom=True,
                amplifier=1.3,
            ))

    return findings


def detect_upgrade_no_timelock(source_code: str, contract_name: str) -> list[SlitherFinding]:
    """
    Detects upgradeable contracts without timelock on the upgrade path.
    Checks each upgrade pattern separately to avoid regex alternation
    issues. Each pattern is a standalone re.search call.
    Amplifier 1.4x — affects entire protocol trustworthiness.
    """
    findings = []

    upgrade_patterns = [
        r'UUPSUpgradeable',
        r'TransparentUpgradeableProxy',
        r'function\s+upgradeTo\s*\(',
        r'function\s+upgradeToAndCall\s*\(',
        r'_authorizeUpgrade\s*\(',
    ]

    is_upgradeable = any(
        re.search(p, source_code, re.IGNORECASE)
        for p in upgrade_patterns
    )

    if not is_upgradeable:
        return findings

    has_timelock = bool(re.search(
        r'TimelockController|ITimelock|MINIMUM_DELAY|TimelockUpgradeable',
        source_code, re.IGNORECASE
    ))

    if not has_timelock:
        findings.append(SlitherFinding(
            check="upgrade-no-timelock",
            impact="Medium",
            confidence="High",
            description=(
                "Contract is upgradeable but the upgrade path has no timelock. "
                "The implementation can be changed immediately by the admin with "
                "no on-chain delay, giving users no time to exit before logic changes."
            ),
            is_custom=True,
            amplifier=1.4,
        ))

    return findings


def _extract_function_bodies(source_code: str, func_names: list[str]) -> list[tuple[str, str]]:
    """
    Extract (function_name, body) pairs for functions whose names match
    any entry in func_names using word boundary matching.
    Uses brace counting to correctly handle nested blocks.
    """
    results = []
    pattern = re.compile(
        r'function\s+(' + '|'.join(func_names) + r')\b',
        re.IGNORECASE
    )

    for match in pattern.finditer(source_code):
        func_name = match.group(1)
        start = source_code.find('{', match.end())
        if start == -1:
            continue

        depth = 0
        end = start
        for i, ch in enumerate(source_code[start:], start=start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break

        body = source_code[start:end + 1]
        results.append((func_name, body))

    return results
