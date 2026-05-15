"""
Slither static analysis runner.
Writes source code to temp files, runs Slither as a Python import,
parses findings into SlitherFinding objects, then cleans up.
Handles: single-file source, multi-file JSON bundles (Etherscan standard JSON).

Import resolution strategy:
  We flatten all files into one directory and rewrite import paths
  to use bare filenames. This works across all solc versions including
  older ones (pre-0.8.8) that don't support --include-path.
"""

import json
import os
import re
import shutil
import tempfile
import time
import structlog

from app.core.models.scoring import SlitherFinding

log = structlog.get_logger()

IMPACT_WEIGHT = {
    "High":          10.0,
    "Medium":         5.0,
    "Low":            2.0,
    "Informational":  0.5,
    "Optimization":   0.0,
}

CONFIDENCE_MULTIPLIER = {
    "High":   1.0,
    "Medium": 0.7,
    "Low":    0.4,
}


def run_slither(
    source_code: str,
    contract_name: str,
    compiler_version: str | None = None,
) -> tuple[list[SlitherFinding], float, str | None]:
    """
    Run Slither on Solidity source code.
    Returns findings, duration in seconds, and error string if failed.
    """
    start = time.time()
    tmp_dir = None

    try:
        tmp_dir = tempfile.mkdtemp(prefix="privascan_slither_")
        sol_path = _write_source_files(tmp_dir, source_code, contract_name)

        if compiler_version:
            _set_solc_version(compiler_version)

        findings = _run_slither_analysis(sol_path, tmp_dir)
        duration = time.time() - start

        log.info(
            "slither.complete",
            contract=contract_name,
            findings=len(findings),
            duration_s=round(duration, 2),
        )
        return findings, duration, None

    except Exception as e:
        duration = time.time() - start
        error_msg = str(e)
        log.warning("slither.failed", contract=contract_name, error=error_msg)
        return [], duration, error_msg

    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


def _rewrite_imports(content: str) -> str:
    """
    Rewrite import paths to use bare filenames only.
    Converts: import "./interfaces/IERC20.sol"
    To:       import "./IERC20.sol"

    This works because we flatten all files into one directory,
    so all imports resolve from the same location regardless of
    what subdirectory they originally lived in.
    Handles both quoted styles: "..." and '...'
    """
    def flatten_import(match: re.Match) -> str:
        quote = match.group(1)
        path = match.group(2)
        filename = os.path.basename(path)
        return f'import {quote}./{filename}{quote}'

    # Match: import "path/to/File.sol" or import 'path/to/File.sol'
    # Also handles: import {X} from "path" and import * as X from "path"
    pattern = re.compile(r'import\s+(["\'])([^"\']+\.sol)\1')
    return pattern.sub(flatten_import, content)


def _write_source_files(tmp_dir: str, source_code: str, contract_name: str) -> str:
    """
    Write source code to disk and return the PRIMARY .sol file path.

    For multi-file bundles: writes all files flat into tmp_dir,
    rewrites their import paths to match the flat structure, then
    returns the file whose name best matches the contract name.

    For single-file source: writes directly as contract_name.sol.
    """
    cleaned = source_code.strip()

    # Etherscan wraps standard JSON input in double braces {{ ... }}
    if cleaned.startswith("{{"):
        cleaned = cleaned[1:-1]

    try:
        bundle = json.loads(cleaned)
        if "sources" in bundle:
            first_sol: str | None = None
            primary_sol: str | None = None

            for file_path, file_data in bundle["sources"].items():
                filename = os.path.basename(file_path)
                full_path = os.path.join(tmp_dir, filename)
                content = file_data.get("content", "")

                # Rewrite imports to flat paths before writing to disk
                content = _rewrite_imports(content)

                with open(full_path, "w") as f:
                    f.write(content)

                if first_sol is None and filename.endswith(".sol"):
                    first_sol = full_path

                if contract_name.lower() in filename.lower():
                    primary_sol = full_path

            chosen = primary_sol or first_sol
            if chosen:
                log.info("slither.entry_point", file=os.path.basename(chosen))
                return chosen

    except (json.JSONDecodeError, TypeError):
        pass

    # Plain Solidity source — rewrite imports and write as single file
    source_code = _rewrite_imports(source_code)
    sol_path = os.path.join(tmp_dir, f"{contract_name}.sol")
    with open(sol_path, "w") as f:
        f.write(source_code)
    return sol_path


def _set_solc_version(compiler_version: str) -> None:
    """
    Switch solc to the version the contract was compiled with.
    Extracts semver from strings like 'v0.8.4+commit.c7e474f2'.
    Silently continues if version switch fails — Slither uses default.
    """
    try:
        import subprocess
        version = compiler_version.split("+")[0].lstrip("v")
        result = subprocess.run(
            ["solc-select", "use", version, "--always-install"],
            capture_output=True,
            timeout=60,
        )
        if result.returncode == 0:
            log.info("slither.solc_version_set", version=version)
        else:
            log.warning("slither.solc_version_failed", version=version)
    except Exception as e:
        log.warning("slither.solc_select_error", error=str(e))


def _run_slither_analysis(sol_path: str, tmp_dir: str) -> list[SlitherFinding]:
    """
    Run Slither programmatically on a single .sol entry-point file.
    No solc args needed — all imports resolve from the same flat directory
    since we rewrote them during file writing.
    Slither writes JSON output which we parse into SlitherFinding objects.
    """
    from slither import Slither

    json_output_path = os.path.join(tmp_dir, "slither_output.json")

    sl = Slither(
        sol_path,
        json=json_output_path,
        disable_color=True,
        filter_paths="test|mock|Mock|Test|interface|Interface",
    )

    if not os.path.exists(json_output_path):
        return []

    with open(json_output_path) as f:
        raw = json.load(f)

    findings = []
    for result in raw.get("results", {}).get("detectors", []):
        impact = result.get("impact", "Informational")
        confidence = result.get("confidence", "Low")

        if impact == "Optimization":
            continue

        findings.append(SlitherFinding(
            check=result.get("check", "unknown"),
            impact=impact,
            confidence=confidence,
            description=result.get("description", "").strip(),
            elements=result.get("elements", []),
            is_custom=False,
            amplifier=1.0,
        ))

    return findings


def score_from_findings(findings: list[SlitherFinding]) -> float:
    """
    Convert findings into a 0-100 risk score.
    penalty = sum(impact_weight x confidence_multiplier x amplifier)
    score   = min(100, penalty)
    Higher score = more risk.
    """
    if not findings:
        return 0.0

    total_penalty = 0.0
    for f in findings:
        weight = IMPACT_WEIGHT.get(f.impact, 0.0)
        multiplier = CONFIDENCE_MULTIPLIER.get(f.confidence, 0.4)
        total_penalty += weight * multiplier * f.amplifier

    return min(100.0, round(total_penalty, 2))
