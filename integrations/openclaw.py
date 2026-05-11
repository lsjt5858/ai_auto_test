from __future__ import annotations

import io
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from config.settings import ROOT_DIR, settings


@dataclass(frozen=True)
class OpenClawResult:
    success: bool
    answer: str
    status_code: int
    request_id: str
    raw: dict[str, Any]


class OpenClawExecutor:
    def execute(self, skill: Any, case: Any, context: dict[str, Any]) -> OpenClawResult:
        started = time.perf_counter()
        command = self._build_command(skill, case, context)
        host = _required(context, "OPENCLAW_HOST")
        username = _required(context, "OPENCLAW_USERNAME")
        port = int(context.get("OPENCLAW_PORT") or 22)
        command_timeout = float(
            context.get("OPENCLAW_COMMAND_TIMEOUT")
            or skill.raw.get("command_timeout_seconds")
            or settings.timeout_seconds
        )

        try:
            client = self._connect(context, host=host, port=port, username=username)
            try:
                _, stdout, stderr = client.exec_command(command, timeout=command_timeout)
                stdout_text = stdout.read().decode("utf-8", errors="replace")
                stderr_text = stderr.read().decode("utf-8", errors="replace")
                exit_status = stdout.channel.recv_exit_status()
            finally:
                client.close()
        except Exception as exc:
            return OpenClawResult(
                success=False,
                answer=f"openclaw execution failed: {type(exc).__name__}: {exc}",
                status_code=-1,
                request_id=uuid4().hex,
                raw={
                    "command": command,
                    "host": host,
                    "port": port,
                    "username": username,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "latency_ms": (time.perf_counter() - started) * 1000,
                },
            )

        answer = stdout_text.strip() or stderr_text.strip()
        if exit_status == 0 and not answer:
            answer = "openclaw remote command completed successfully"

        return OpenClawResult(
            success=exit_status == 0,
            answer=answer,
            status_code=exit_status,
            request_id=uuid4().hex,
            raw={
                "command": command,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_status": exit_status,
                "host": host,
                "port": port,
                "username": username,
                "strict_host_key": _as_bool(context.get("OPENCLAW_STRICT_HOST_KEY"), default=True),
                "latency_ms": (time.perf_counter() - started) * 1000,
            },
        )

    def _connect(self, context: dict[str, Any], *, host: str, port: int, username: str) -> Any:
        try:
            import paramiko
        except ModuleNotFoundError as exc:
            raise RuntimeError("paramiko is required for openclaw execution; install requirements.txt") from exc

        password = context.get("OPENCLAW_PASSWORD") or None
        pkey = _load_private_key(paramiko, context)
        if not password and pkey is None:
            raise ValueError("openclaw requires OPENCLAW_PASSWORD or OPENCLAW_PRIVATE_KEY_FILE/OPENCLAW_PRIVATE_KEY")

        client = paramiko.SSHClient()
        known_hosts = context.get("OPENCLAW_KNOWN_HOSTS")
        if known_hosts:
            known_hosts_path = Path(str(known_hosts)).expanduser()
            if not known_hosts_path.is_absolute():
                known_hosts_path = ROOT_DIR / known_hosts_path
            client.load_host_keys(str(known_hosts_path))
        else:
            client.load_system_host_keys()

        strict_host_key = _as_bool(context.get("OPENCLAW_STRICT_HOST_KEY"), default=True)
        client.set_missing_host_key_policy(paramiko.RejectPolicy() if strict_host_key else paramiko.AutoAddPolicy())

        connect_timeout = float(context.get("OPENCLAW_CONNECT_TIMEOUT") or settings.timeout_seconds)
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            pkey=pkey,
            timeout=connect_timeout,
            banner_timeout=connect_timeout,
            auth_timeout=connect_timeout,
            look_for_keys=False,
            allow_agent=False,
        )
        return client

    def _build_command(self, skill: Any, case: Any, context: dict[str, Any]) -> str:
        values = dict(context)
        values.update(getattr(case, "raw", {}))
        values["question"] = getattr(case, "question", "")

        command = (
            getattr(case, "input_params", {}).get("openclaw_command")
            or getattr(case, "input_params", {}).get("remote_command")
            or getattr(case, "input_params", {}).get("command")
            or getattr(case, "raw", {}).get("openclaw_command")
            or getattr(case, "raw", {}).get("remote_command")
            or getattr(case, "raw", {}).get("command")
            or skill.raw.get("command_template")
            or "{question}"
        )
        return _format_known_placeholders(str(command), values)


def _load_private_key(paramiko: Any, context: dict[str, Any]) -> Any:
    private_key_text = context.get("OPENCLAW_PRIVATE_KEY") or ""
    private_key_file = context.get("OPENCLAW_PRIVATE_KEY_FILE") or ""
    passphrase = context.get("OPENCLAW_PASSPHRASE") or None

    if private_key_file:
        key_path = Path(str(private_key_file)).expanduser()
        if not key_path.is_absolute():
            key_path = ROOT_DIR / key_path
        private_key_text = key_path.read_text(encoding="utf-8")
    if not private_key_text:
        return None

    last_error: Exception | None = None
    for key_cls in (paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey, paramiko.DSSKey):
        try:
            return key_cls.from_private_key(io.StringIO(str(private_key_text)), password=passphrase)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"failed to load openclaw private key: {last_error}")


def _required(context: dict[str, Any], key: str) -> str:
    value = context.get(key)
    if value in (None, ""):
        raise ValueError(f"missing required openclaw param: {key}")
    return str(value)


def _as_bool(value: Any, *, default: bool) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "n"}


def _format_known_placeholders(command: str, values: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values.get(key, match.group(0)))

    return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, command)
