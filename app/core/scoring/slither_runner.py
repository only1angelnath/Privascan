"""
Slither static analysis runner.
Writes source code to temp files, runs Slither as a Python import,
parses findings into SlitherFinding objects, then cleans up.
Handles: single-file source, multi-file JSON bundles (Etherscan standard JSON).

Import resolution strategy:
  We flatten all files into one directory and rewrite import paths
  to use bare filenames. This works across all solc versions including
  older ones (pre-0.8.8) that don't support --include-path.

OpenZeppelin resolution:
  @openzeppelin/ imports are resolved via a solc remap pointing at
  /app/node_modules, which is pre-installed in the Docker image.
  No npm install is needed at scan time.
"""

import asyncio
import concurrent.futures
import importlib
import inspect
import json
import os
import pkgutil
import re
import shutil
import subprocess
import tempfile
import time
import structlog

from app.core.models.scoring import SlitherFinding

log = structlog.get_logger()

# Path where npm packages are pre-installed in the Docker image (see Dockerfile).
# Used to build solc remaps for @openzeppelin and other node_modules imports.
NODE_MODULES_PATH = os.environ.get("NODE_MODULES_PATH", "/app/node_modules")

# Packages whose imports are rewritten via solc remaps.
# Key = import prefix (e.g. "@openzeppelin/"), value = subfolder under NODE_MODULES_PATH.
REMAP_PACKAGES = {
    "@openzeppelin/": "@openzeppelin/",
    "@uniswap/":      "@uniswap/",
    "@chainlink/":    "@chainlink/",
}

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


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def run_slither(
    source_code: str,
    contract_name: str,
    compiler_version: str | None = None,
) -> tuple[list[SlitherFinding], float, str | None]:
    """
    Run Slither on Solidity source code.
    Returns (findings, duration_seconds, error_string_or_None).
    """
    start   = time.time()
    tmp_dir = None

    try:
        tmp_dir  = tempfile.mkdtemp(prefix="privascan_slither_")
        sol_path = _write_source_files(tmp_dir, source_code, contract_name)

        if compiler_version:
            _set_solc_version(compiler_version)

        findings = _run_slither_analysis(sol_path, source_code)
        duration = time.time() - start

        log.info(
            "slither.complete",
            contract=contract_name,
            findings=len(findings),
            duration_s=round(duration, 2),
        )
        return findings, duration, None

    except Exception as exc:
        duration  = time.time() - start
        error_msg = str(exc)
        log.warning("slither.failed", contract=contract_name, error=error_msg)
        return [], duration, error_msg

    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT REWRITING
# ─────────────────────────────────────────────────────────────────────────────

def _rewrite_imports(content: str) -> str:
    """
    Rewrite *relative* import paths to bare filenames so that Slither
    can resolve them from the flat tmp_dir layout.

    Handles all four Solidity import forms:
      import "./path/to/File.sol";
      import "./path/to/File.sol" as Foo;
      import {Symbol} from "./path/to/File.sol";
      import * as Foo from "./path/to/File.sol";

    Node-modules imports (@openzeppelin/…) are intentionally left
    unchanged — they are resolved via solc remaps instead.
    """
    # Matches both `import "..."` and `... from "..."` but only for
    # relative paths (starting with . or /) — not @-scoped packages.
    pattern = re.compile(
        r'(?:from\s+|import\s+(?:[^"\']*?\s+from\s+)?)(["\'])(\./[^"\']+\.sol|/[^"\']+\.sol)\1'
    )

    def flatten_import(match: re.Match) -> str:
        quote    = match.group(1)
        path     = match.group(2)
        filename = os.path.basename(path)
        original = match.group(0)
        return original.replace(f"{quote}{path}{quote}", f"{quote}./{filename}{quote}")

    return pattern.sub(flatten_import, content)


# ─────────────────────────────────────────────────────────────────────────────
# FILE WRITING
# ─────────────────────────────────────────────────────────────────────────────

def _write_source_files(tmp_dir: str, source_code: str, contract_name: str) -> str:
    """
    Write source code to disk and return the PRIMARY .sol file path.

    Multi-file bundle (Etherscan standard JSON):
      - Flattens all files into tmp_dir
      - Rewrites relative imports to flat paths
      - Returns the file whose name best matches contract_name

    Single-file source:
      - Writes directly as <contract_name>.sol
    """
    cleaned = source_code.strip()

    # Etherscan sometimes wraps standard JSON in double braces
    if cleaned.startswith("{{"):
        cleaned = cleaned[1:-1]

    try:
        bundle = json.loads(cleaned)
        if "sources" in bundle:
            first_sol:   str | None = None
            primary_sol: str | None = None

            for file_path, file_data in bundle["sources"].items():
                filename  = os.path.basename(file_path)
                full_path = os.path.join(tmp_dir, filename)
                content   = file_data.get("content", "")
                content   = _rewrite_imports(content)

                with open(full_path, "w") as fh:
                    fh.write(content)

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

    # Plain Solidity source
    source_code = _rewrite_imports(source_code)
    sol_path    = os.path.join(tmp_dir, f"{contract_name}.sol")
    with open(sol_path, "w") as fh:
        fh.write(source_code)
    return sol_path


# ─────────────────────────────────────────────────────────────────────────────
# SOLC VERSION SWITCHING
# ─────────────────────────────────────────────────────────────────────────────

def _set_solc_version(compiler_version: str) -> None:
    """
    Switch solc to the version the contract was compiled with.
    Extracts semver from strings like 'v0.8.4+commit.c7e474f2'.

    Runs in a ThreadPoolExecutor so it never blocks an async event loop.
    Silently continues on failure — Slither falls back to the default solc.
    """
    try:
        version = compiler_version.split("+")[0].lstrip("v")

        def _run() -> subprocess.CompletedProcess:
            return subprocess.run(
                ["solc-select", "use", version, "--always-install"],
                capture_output=True,
                timeout=60,
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(_run).result(timeout=65)
        else:
            result = _run()

        if result.returncode == 0:
            log.info("slither.solc_version_set", version=version)
        else:
            log.warning(
                "slither.solc_version_failed",
                version=version,
                stderr=result.stderr.decode(errors="replace")[:200],
            )
    except Exception as exc:
        log.warning("slither.solc_select_error", error=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# OPENZEPPELIN / NODE_MODULES REMAPS
# ─────────────────────────────────────────────────────────────────────────────

def _build_remaps(source_code: str) -> list[str]:
    """
    Build solc import remappings for any node_modules packages referenced
    in the source.  The packages are pre-installed at NODE_MODULES_PATH
    in the Docker image — no npm install is needed at scan time.

    Example output:
      ["@openzeppelin/=/app/node_modules/@openzeppelin/"]
    """
    remaps = []
    for prefix, folder in REMAP_PACKAGES.items():
        if prefix in source_code:
            target = os.path.join(NODE_MODULES_PATH, folder)
            if os.path.isdir(target):
                remaps.append(f"{prefix}={target}")
                log.info("slither.remap_added", prefix=prefix, target=target)
            else:
                log.warning(
                    "slither.remap_missing",
                    prefix=prefix,
                    target=target,
                    hint="Add 'npm install --prefix /app <pkg>' to Dockerfile",
                )
    return remaps


# ─────────────────────────────────────────────────────────────────────────────
# DETECTOR LOADING
# ─────────────────────────────────────────────────────────────────────────────

def _load_all_detectors() -> list:
    """
    Dynamically discover all AbstractDetector subclasses from
    slither.detectors.*  — mirrors what the Slither CLI loads by default.
    """
    import slither.detectors as det_pkg
    from slither.detectors.abstract_detector import AbstractDetector

    detectors: list = []
    for _imp, modname, _ispkg in pkgutil.walk_packages(
        path=det_pkg.__path__,
        prefix=det_pkg.__name__ + ".",
        onerror=lambda _: None,
    ):
        try:
            module = importlib.import_module(modname)
            for _name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, AbstractDetector)
                    and obj is not AbstractDetector
                    and obj.__module__ == modname
                ):
                    detectors.append(obj)
        except Exception:
            pass

    return detectors


# ─────────────────────────────────────────────────────────────────────────────
# SLITHER ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def _run_slither_analysis(sol_path: str, source_code: str) -> list[SlitherFinding]:
    """
    Run Slither programmatically on a single .sol entry-point file.

    Key design decisions:
      - No `json=` kwarg (invalid in Slither Python API)
      - solc_remaps built from source_code so @openzeppelin/... resolves
        against the pre-installed node_modules in the Docker image
      - filter_paths is a list[str] (Slither kwarg expects a list, not a
        pipe-delimited string)
      - All detectors registered explicitly; run_detectors() called and
        its list[list[dict]] return value iterated for findings
    """
    from slither import Slither

    remaps = _build_remaps(source_code)

    slither_kwargs: dict = dict(
        filter_paths    = ["test", "mock", "Mock", "Test", "interface", "Interface"],
        exclude_dependencies = True,
        disable_color   = True,
    )
    if remaps:
        slither_kwargs["solc_remaps"] = remaps

    sl = Slither(sol_path, **slither_kwargs)

    # Register all available detectors (mirrors CLI with no --detect filter)
    for detector_cls in _load_all_detectors():
        try:
            sl.register_detector(detector_cls)
        except Exception:
            pass  # silently skip duplicates / incompatible detectors

    # run_detectors() returns list[list[dict]] — one inner list per detector
    raw_results: list[list[dict]] = sl.run_detectors()

    findings: list[SlitherFinding] = []
    for detector_results in raw_results:
        for result in detector_results:
            impact     = result.get("impact",     "Informational")
            confidence = result.get("confidence", "Low")

            if impact == "Optimization":
                continue

            findings.append(SlitherFinding(
                check       = result.get("check", "unknown"),
                impact      = impact,
                confidence  = confidence,
                description = result.get("description", "").strip(),
                elements    = result.get("elements", []),
                is_custom   = False,
                amplifier   = 1.0,
            ))

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────────────────

def score_from_findings(findings: list[SlitherFinding]) -> float:
    """
    Convert findings into a 0–100 risk score.
    penalty = sum(impact_weight × confidence_multiplier × amplifier)
    score   = min(100, penalty)
    Higher score = more risk.
    """
    if not findings:
        return 0.0

    total_penalty = sum(
        IMPACT_WEIGHT.get(f.impact, 0.0)
        * CONFIDENCE_MULTIPLIER.get(f.confidence, 0.4)
        * f.amplifier
        for f in findings
    )
    return min(100.0, round(total_penalty, 2))