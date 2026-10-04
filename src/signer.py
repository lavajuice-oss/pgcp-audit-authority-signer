#!/usr/bin/env python3
"""Restricted PGCP Audit Authority signer reference implementation.

Production secret material is supplied only through AUDIT_AUTHORITY_KEY_PEM_B64.
This program never prints the secret and will not expose a generic byte-signing API.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_FILE = ROOT / "config" / "v1.36-authorized-subject.json"
POLICY_FILE = ROOT / "policy" / "signer-policy.json"
EXPECTED_PUB_B64 = "pL/WL+tAdGVTINzs3J6uCr9btmHYK1Y9gDNhzpJbGlo="


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_public_subject() -> tuple[dict[str, Any], dict[str, Any]]:
    return json.loads(SUBJECT_FILE.read_text(encoding="utf-8")), json.loads(POLICY_FILE.read_text(encoding="utf-8"))


def load_key_from_env() -> Ed25519PrivateKey:
    value = os.environ.get("AUDIT_AUTHORITY_KEY_PEM_B64")
    if not value:
        raise RuntimeError("AUDIT_AUTHORITY_KEY_PEM_B64 is unavailable")
    try:
        pem = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise RuntimeError("custody secret is not valid base64") from exc
    key = serialization.load_pem_private_key(pem, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise RuntimeError("custody secret is not an Ed25519 private key")
    return key


def public_b64(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode("ascii")


def public_fingerprint(public_key_b64: str) -> str:
    return sha256_bytes(base64.b64decode(public_key_b64))


def load_request(path: Path) -> dict[str, Any]:
    request = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise RuntimeError("request must be a JSON object")
    return request


def validate_subject(request: dict[str, Any], subject: dict[str, Any]) -> None:
    s = subject["subject"]
    checks = {
        "package_id": s["package_id"],
        "package_version": s["package_version"],
        "archive_sha256": s["archive_sha256"],
        "root_manifest_sha256": s["root_manifest_sha256"],
        "root_anchor_sha256": s["root_anchor_sha256"],
        "proposal_id": s["proposal_id"],
        "proposal_raw_sha256": s["proposal_raw_sha256"],
        "predecessor_pointer_raw_sha256": s["predecessor_pointer_raw_sha256"],
        "audit_id": s["audit_id"],
        "audit_version": s["audit_version"],
        "audit_raw_sha256": s["audit_raw_sha256"],
        "audit_disposition": s["audit_disposition"],
    }
    for key, expected in checks.items():
        if request.get(key) != expected:
            raise RuntimeError(f"subject mismatch: {key}")
    if request.get("operation") != "issue_audit_disposition":
        raise RuntimeError("unauthorized operation")
    if request.get("authority_role") != "AUDIT_AUTHORITY":
        raise RuntimeError("unauthorized authority role")
    if request.get("acceptance") not in (None, False):
        raise RuntimeError("acceptance is outside signer authority")
    if request.get("promotion") not in (None, False):
        raise RuntimeError("promotion is outside signer authority")


def verify_custody() -> dict[str, Any]:
    subject, policy = load_public_subject()
    key = load_key_from_env()
    derived = public_b64(key)
    match = derived == EXPECTED_PUB_B64 == subject["audit_authority"]["public_key_b64"]
    result = {
        "artifact_type": "PGCP_AA_CUSTODY_VERIFICATION_RESULT",
        "version": "v0.1",
        "result": "PASS" if match else "BLOCKED",
        "command_id": "VERIFY_PRODUCTION_CUSTODY",
        "key_strategy": policy["key_strategy"],
        "trust_root_binding": subject["trust_root_binding"],
        "expected_public_key_b64": EXPECTED_PUB_B64,
        "derived_public_key_b64": derived,
        "public_key_fingerprint_sha256": public_fingerprint(derived),
        "public_key_match": match,
        "private_key_exported": False,
        "private_key_material_in_output": False,
        "repository_source_control_secret": False,
        "next_gate": "PKE_ELIGIBILITY_RECONCILIATION" if match else "BLOCKED",
        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if not match:
        raise RuntimeError("derived public key does not equal fixed v1.36 trust root")
    return result


def issue_shadow(request_path: Path) -> dict[str, Any]:
    subject, policy = load_public_subject()
    # Shadow mode uses an explicitly synthetic key supplied by the caller.
    shadow_key = Ed25519PrivateKey.generate()
    if public_b64(shadow_key) == EXPECTED_PUB_B64:
        raise RuntimeError("synthetic key unexpectedly equals production trust root")
    request = load_request(request_path)
    validate_subject(request, subject)
    unsigned = {k: v for k, v in request.items() if k != "signature_b64"}
    payload = canonical(unsigned)
    signature = shadow_key.sign(payload)
    verified = shadow_key.public_key().verify(signature, payload) is None
    result = {
        "artifact_type": "PGCP_AA_SHADOW_SIGNING_RESULT",
        "version": "v0.1",
        "result": "PASS" if verified else "BLOCKED",
        "command_id": "ISSUE_AUDIT_DISPOSITION",
        "operation": "issue_audit_disposition",
        "shadow_only": True,
        "production_authority": False,
        "production_eligibility": False,
        "public_key_b64": public_b64(shadow_key),
        "shadow_key_equals_v1_36_root": False,
        "canonical_request_sha256": sha256_bytes(payload),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "private_key_exported": False,
        "private_key_material_in_output": False,
        "generic_signing_oracle": policy["generic_signing_oracle"],
        "next_gate": "GITHUB_PRODUCTION_CUSTODY_CONFIGURATION",
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("verify-custody")
    shadow = sub.add_parser("issue-shadow")
    shadow.add_argument("request", type=Path)
    args = ap.parse_args()

    try:
        if args.command == "verify-custody":
            out = verify_custody()
        else:
            out = issue_shadow(args.request)
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "artifact_type": "PGCP_AA_SIGNER_RESULT",
            "version": "v0.1",
            "result": "BLOCKED",
            "reason": str(exc),
            "private_key_exported": False,
            "private_key_material_in_output": False
        }, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
