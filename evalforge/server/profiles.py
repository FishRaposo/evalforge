"""Validated local upload profiles with immutable inputs and explicit retention."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from evalforge.storage.history import database_connection

SUITE_LIMIT = 2 * 1024 * 1024
RESPONSE_LIMIT = 10 * 1024 * 1024


def input_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_upload_yaml(raw: bytes) -> None:
    """Reject executable tags, aliases, includes and external execution references."""
    text = raw.decode("utf-8")
    tokens = list(yaml.scan(text))
    if len(tokens) > 100_000 or any(
        isinstance(token, yaml.tokens.AliasToken) for token in tokens
    ):
        raise ValueError("YAML aliases and oversized structures are not supported")
    nesting = 0
    for token in tokens:
        if isinstance(
            token,
            (
                yaml.tokens.BlockMappingStartToken,
                yaml.tokens.BlockSequenceStartToken,
                yaml.tokens.FlowMappingStartToken,
                yaml.tokens.FlowSequenceStartToken,
            ),
        ):
            nesting += 1
            if nesting > 30:
                raise ValueError("Suite nesting exceeds 30 levels")
        elif isinstance(
            token,
            (
                yaml.tokens.BlockEndToken,
                yaml.tokens.FlowMappingEndToken,
                yaml.tokens.FlowSequenceEndToken,
            ),
        ):
            nesting -= 1
    document = yaml.safe_load(text)
    if not isinstance(document, dict):
        raise ValueError("Suite must be a YAML mapping")
    _check_yaml_tree(document)


def _check_yaml_tree(document: dict[str, Any]) -> None:
    stack: list[tuple[Any, int]] = [(document, 0)]
    while stack:
        value, depth = stack.pop()
        if depth > 30:
            raise ValueError("Suite nesting exceeds 30 levels")
        if isinstance(value, dict):
            for key, child in value.items():
                name = str(key).lower()
                if name in {
                    "include",
                    "includes",
                    "plugin",
                    "plugins",
                    "provider",
                    "file",
                    "path",
                } or name.endswith(("_path", "_file")):
                    raise ValueError(
                        "Includes, plugins and external references are forbidden"
                    )
                if name == "backend" and child is not None and child != "saved":
                    raise ValueError(
                        "Web profiles only support the saved response backend"
                    )
                stack.append((child, depth + 1))
        elif isinstance(value, list):
            stack.extend((child, depth + 1) for child in value)


class ProfileManager:
    """Keep uploaded inputs until the operator explicitly performs manual cleanup."""

    def __init__(self, db_path: str, root: Path) -> None:
        self.db_path = db_path
        self.root = root.expanduser().resolve()
        self._builtins: dict[str, dict[str, Any]] | None = None
        with database_connection(db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS evaluation_profiles (
                id TEXT PRIMARY KEY, descriptor_json TEXT NOT NULL,
                suite_name TEXT NOT NULL, response_name TEXT NOT NULL)""")

    def _load_builtins(self) -> dict[str, dict[str, Any]]:
        if self._builtins is None:
            from evalforge.evaluation import validate_saved_inputs
            from evalforge.portfolio import get_portfolio_profiles

            profiles = {}
            for source in get_portfolio_profiles():
                info = validate_saved_inputs(
                    source["suite_path"], source["response_path"], web=True
                )
                info = {
                    **info,
                    "provenance": {
                        **info.get("provenance", {}),
                        **source.get("provenance", {}),
                        "assessed_response_origin": info.get("provenance", {}).get(
                            "origin", "unknown"
                        ),
                    },
                }
                descriptor = self._descriptor(
                    source["id"],
                    source["name"],
                    source["description"],
                    info,
                    source["suite_path"],
                    source["response_path"],
                    False,
                )
                profiles[source["id"]] = {
                    **descriptor,
                    "suite_path": source["suite_path"],
                    "response_path": source["response_path"],
                }
            self._builtins = profiles
        return self._builtins

    @staticmethod
    def _descriptor(
        profile_id: str,
        name: str,
        description: str,
        info: dict[str, Any],
        suite: Path,
        responses: Path,
        uploaded: bool,
    ) -> dict[str, Any]:
        provenance = info.get("provenance", {})
        return {
            "id": profile_id,
            "name": name,
            "description": description,
            "origin": provenance.get("origin", "unknown"),
            "dataset_revision": info.get("dataset_revision"),
            "case_count": info["case_count"],
            "uploaded": uploaded,
            "input_hashes": {
                "suite": input_hash(suite),
                "responses": input_hash(responses),
            },
            "provenance": provenance,
            "retention": "Inputs are retained locally until manual cleanup",
        }

    @staticmethod
    def public(profile: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in profile.items()
            if key not in {"suite_path", "response_path"}
        }

    def _contained(self, relative: str) -> Path:
        target = self.root / relative
        if target.is_symlink() or not target.resolve().is_relative_to(self.root):
            raise ValueError("Stored upload is outside its configured directory")
        return target

    def list(self) -> list[dict[str, Any]]:
        """Return public descriptors without absolute host paths."""
        result = [self.public(profile) for profile in self._load_builtins().values()]
        with database_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT descriptor_json FROM evaluation_profiles ORDER BY id"
            ).fetchall()
        return result + [json.loads(row[0]) for row in rows]

    def get(self, profile_id: str) -> dict[str, Any] | None:
        with database_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT descriptor_json,suite_name,response_name "
                "FROM evaluation_profiles WHERE id=?",
                (profile_id,),
            ).fetchone()
        if row:
            return {
                **json.loads(row[0]),
                "suite_path": self._contained(row[1]),
                "response_path": self._contained(row[2]),
            }
        return self._load_builtins().get(profile_id)

    def validate(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Recheck hashes and strict schema before claiming a job."""
        from evalforge.evaluation import validate_saved_inputs

        suite, responses = profile["suite_path"], profile["response_path"]
        if (
            suite.stat().st_size > SUITE_LIMIT
            or responses.stat().st_size > RESPONSE_LIMIT
        ):
            raise ValueError("Profile input exceeds the local upload byte cap")
        if profile["input_hashes"] != {
            "suite": input_hash(suite),
            "responses": input_hash(responses),
        }:
            raise ValueError("Profile inputs changed; upload a new validated profile")
        check_upload_yaml(suite.read_bytes())
        return validate_saved_inputs(suite, responses, web=True)

    def upload(self, suite_raw: bytes, response_raw: bytes) -> dict[str, Any]:
        """Store only validated input pairs in server-generated UUID directories."""
        if len(suite_raw) > SUITE_LIMIT or len(response_raw) > RESPONSE_LIMIT:
            raise ValueError("Input exceeds the local upload byte cap")
        check_upload_yaml(suite_raw)
        response_raw.decode("utf-8")
        self.root.mkdir(parents=True, exist_ok=True)
        profile_id = str(uuid4())
        directory = self.root / profile_id
        directory.mkdir()
        suite, responses = directory / "suite.yaml", directory / "responses.jsonl"
        try:
            suite.write_bytes(suite_raw)
            responses.write_bytes(response_raw)
            from evalforge.evaluation import validate_saved_inputs

            info = validate_saved_inputs(suite, responses, web=True)
            descriptor = self._descriptor(
                profile_id,
                "Uploaded response profile",
                "Locally uploaded suite and saved responses",
                info,
                suite,
                responses,
                True,
            )
            with database_connection(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO evaluation_profiles VALUES (?,?,?,?)",
                    (
                        profile_id,
                        json.dumps(descriptor),
                        f"{profile_id}/suite.yaml",
                        f"{profile_id}/responses.jsonl",
                    ),
                )
            return descriptor
        except Exception:
            suite.unlink(missing_ok=True)
            responses.unlink(missing_ok=True)
            directory.rmdir()
            raise
