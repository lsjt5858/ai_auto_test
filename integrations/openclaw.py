from __future__ import annotations

import io
import json
import re
import shlex
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

        parsed = _parse_agent_json(stdout_text) if _is_agent_mode(skill, context) else {}
        answer = _extract_agent_answer(parsed) or stdout_text.strip() or stderr_text.strip()
        if exit_status == 0 and not answer:
            answer = "openclaw remote command completed successfully"

        return OpenClawResult(
            success=exit_status == 0 and str(parsed.get("status", "ok")).lower() != "error",
            answer=answer,
            status_code=exit_status,
            request_id=uuid4().hex,
            raw={
                "command": command,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_status": exit_status,
                "agent_json": parsed,
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
        if _is_agent_mode(skill, context):
            return self._build_agent_command(skill, case, context)

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

    def _build_agent_command(self, skill: Any, case: Any, context: dict[str, Any]) -> str:
        values = dict(context)
        values.update(getattr(case, "raw", {}))
        values["question"] = getattr(case, "question", "")

        message = (
            getattr(case, "input_params", {}).get("openclaw_task")
            or getattr(case, "input_params", {}).get("agent_message")
            or getattr(case, "raw", {}).get("openclaw_task")
            or getattr(case, "raw", {}).get("agent_message")
            or skill.raw.get("agent_task_template")
            or "{question}"
        )
        message = _format_known_placeholders(str(message), values)
        agent_name = str(context.get("OPENCLAW_AGENT_NAME") or skill.raw.get("agent_name") or "main")
        agent_timeout = int(
            float(
                context.get("OPENCLAW_AGENT_TIMEOUT")
                or context.get("OPENCLAW_COMMAND_TIMEOUT")
                or skill.raw.get("agent_timeout_seconds")
                or skill.raw.get("command_timeout_seconds")
                or 180
            )
        )

        return " ".join(
            [
                "openclaw",
                "agent",
                "--agent",
                shlex.quote(agent_name),
                "-m",
                shlex.quote(message),
                "--timeout",
                str(agent_timeout),
                "--json",
            ]
        )


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


def _is_agent_mode(skill: Any, context: dict[str, Any]) -> bool:
    mode = context.get("OPENCLAW_MODE") or getattr(skill, "raw", {}).get("openclaw_mode")
    return str(mode or "").strip().lower() == "agent"


def _parse_agent_json(stdout_text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(stdout_text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout_text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and ("result" in value or "status" in value):
            return value
    return {}


def _extract_agent_answer(agent_json: dict[str, Any]) -> str:
    payloads = agent_json.get("result", {}).get("payloads", []) if agent_json else []
    texts = [str(item.get("text", "")).strip() for item in payloads if isinstance(item, dict) and item.get("text")]
    return "\n\n".join(text for text in texts if text)
