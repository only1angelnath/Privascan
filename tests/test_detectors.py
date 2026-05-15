"""
Unit test for all 5 privacy detectors using deliberately vulnerable mock source.
This confirms detectors fire correctly — independent of real contract quality.
"""

from app.core.detectors.privacy_detectors import run_all_privacy_detectors

# Deliberately vulnerable mock privacy pool source code
# Contains all 5 vulnerability patterns our detectors look for
VULNERABLE_SOURCE = """
pragma solidity ^0.8.0;

interface IVerifier {
    function verifyProof(bytes memory proof) external returns (bool);
}

contract VulnerablePrivacyPool {

    IVerifier public verifier;
    mapping(bytes32 => bool) public nullifierHashes;
    address public owner;

    // VULNERABILITY 1: admin can replace verifier (zk-verifier-bypass)
    function setVerifier(address _newVerifier) external onlyOwner {
        verifier = IVerifier(_newVerifier);
    }

    // VULNERABILITY 2: verifier result not checked (zk-verifier-bypass)
    function deposit(bytes memory proof) external {
        verifier.verifyProof(proof);  // return value ignored!
        // continues regardless of proof validity
    }

    // VULNERABILITY 3: mixer reentrancy — external call before nullifier update
    // VULNERABILITY 4: nullifier check missing in withdraw
    function withdraw(bytes32 nullifierHash, address payable recipient) external {
        // external call BEFORE nullifier is marked spent
        (bool success, ) = recipient.call{value: 1 ether}("");
        require(success);
        // nullifier updated AFTER the call — reentrancy window!
        nullifierHashes[nullifierHash] = true;
    }

    // VULNERABILITY 5: admin can pause without timelock (admin-key-risk)
    function pause() external onlyOwner {
        // no timelock
    }

    // VULNERABILITY 5b: admin can drain (admin-key-risk)
    function drain() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    // upgradeable without timelock (upgrade-no-timelock)
    function upgradeTo(address newImpl) external onlyOwner {
        // UUPS pattern but no timelock
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
}
"""

def main():
    print("\n── Privacy Detector Unit Tests ───────────────────")
    print("Testing against deliberately vulnerable mock contract")
    print("──────────────────────────────────────────────────\n")

    findings = run_all_privacy_detectors(VULNERABLE_SOURCE, "VulnerablePrivacyPool")

    print(f"Total findings: {len(findings)}\n")

    checks_found = set()
    for f in findings:
        checks_found.add(f.check)
        print(f"  ✓ [{f.impact}/{f.confidence}] {f.check} (amplifier={f.amplifier})")
        print(f"    {f.description[:120]}")
        print()

    print("── Coverage ───────────────────────────────────────")
    expected = {
        "mixer-reentrancy",
        "zk-verifier-bypass",
        "nullifier-reuse",
        "admin-key-risk",
        "upgrade-no-timelock",
    }
    for check in expected:
        status = "✓ FIRED" if check in checks_found else "✗ MISSED"
        print(f"  {status}  {check}")

    missed = expected - checks_found
    if not missed:
        print("\n All 5 detectors fired correctly ✓")
    else:
        print(f"\n  {len(missed)} detector(s) missed: {missed}")

    print("──────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
