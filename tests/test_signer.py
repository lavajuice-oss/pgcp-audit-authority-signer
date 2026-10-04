from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
SIGNER = ROOT / "src" / "signer.py"
SUBJECT = json.loads((ROOT / "config" / "v1.36-authorized-subject.json").read_text())


def base_request() -> dict:
    s = SUBJECT["subject"]
    return {
        "operation": "issue_audit_disposition",
        "authority_role": "AUDIT_AUTHORITY",
        **s,
        "acceptance": None,
        "promotion": None,
        "signature_b64": None,
        "request_id": "SHADOW-001"
    }


def test_shadow_signer_passes_and_never_uses_prod_root(tmp_path: Path):
    req = tmp_path / "request.json"
    req.write_text(json.dumps(base_request()), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SIGNER), "issue-shadow", str(req)], capture_output=True, text=True, check=False)
    assert p.returncode == 0, p.stdout + p.stderr
    out = json.loads(p.stdout)
    assert out["result"] == "PASS"
    assert out["shadow_only"] is True
    assert out["production_authority"] is False
    assert out["shadow_key_equals_v1_36_root"] is False
    assert out["private_key_material_in_output"] is False


def test_shadow_signer_rejects_generic_signing(tmp_path: Path):
    req = base_request()
    req["operation"] = "sign_arbitrary_bytes"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(req), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SIGNER), "issue-shadow", str(path)], capture_output=True, text=True, check=False)
    assert p.returncode != 0
    out = json.loads(p.stdout)
    assert out["result"] == "BLOCKED"


def test_shadow_signer_rejects_wrong_v1_36_scope(tmp_path: Path):
    req = base_request()
    req["package_version"] = "v1.35"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(req), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SIGNER), "issue-shadow", str(path)], capture_output=True, text=True, check=False)
    assert p.returncode != 0
    out = json.loads(p.stdout)
    assert out["result"] == "BLOCKED"


def test_verify_custody_with_synthetic_key_is_blocked(tmp_path: Path):
    key = Ed25519PrivateKey.generate()
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    env = dict(os.environ)
    env["AUDIT_AUTHORITY_KEY_PEM_B64"] = base64.b64encode(pem).decode("ascii")
    p = subprocess.run([sys.executable, str(SIGNER), "verify-custody"], capture_output=True, text=True, env=env, check=False)
    assert p.returncode != 0
    out = json.loads(p.stdout)
    assert out["result"] == "BLOCKED"
