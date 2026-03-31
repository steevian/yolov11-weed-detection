#!/usr/bin/env python3
"""Interactive skill installer.

Supports two input styles:
1) Raw address (SSH/HTTPS), for example:
   git@github.com:anthropics/skills.git
   https://github.com/inferen-sh/skills
   -> script runs: npx skills add <address> -g -y

2) Full install command, for example:
   npx skills add https://github.com/inferen-sh/skills --skill nano-banana-2
   -> script executes the command directly.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


def configure_utf8_stdio() -> None:
	"""Force UTF-8 stdio and console code page to minimize mojibake."""
	os.environ.setdefault("PYTHONUTF8", "1")
	os.environ.setdefault("PYTHONIOENCODING", "utf-8")
	if os.name == "nt":
		# Best-effort UTF-8 code page setup for Windows terminals.
		try:
			subprocess.run(["cmd", "/c", "chcp 65001>nul"], check=False)
		except Exception:
			pass
		try:
			import ctypes

			ctypes.windll.kernel32.SetConsoleOutputCP(65001)
			ctypes.windll.kernel32.SetConsoleCP(65001)
		except Exception:
			pass
	try:
		sys.stdout.reconfigure(encoding="utf-8", errors="replace")
		sys.stderr.reconfigure(encoding="utf-8", errors="replace")
		sys.stdin.reconfigure(encoding="utf-8", errors="replace")
	except Exception:
		pass


def decode_output(data: bytes) -> str:
	if not data:
		return ""
	for enc in ("utf-8", "gbk", "cp936", sys.getdefaultencoding()):
		try:
			return data.decode(enc)
		except Exception:
			continue
	return data.decode("utf-8", errors="replace")


def run_cmd(
	cmd: Sequence[str],
	check: bool = True,
	extra_env: Dict[str, str] | None = None,
) -> Tuple[int, str]:
	resolved_cmd = list(cmd)
	if os.name == "nt" and resolved_cmd and resolved_cmd[0].lower() == "npx":
		npx_path = shutil.which("npx.cmd") or shutil.which("npx")
		if npx_path:
			resolved_cmd[0] = npx_path

	env = os.environ.copy()
	if extra_env:
		env.update(extra_env)

	proc = subprocess.run(
		resolved_cmd,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		env=env,
		shell=False,
		check=False,
	)
	out = decode_output(proc.stdout)
	err = decode_output(proc.stderr)
	merged = (out + ("\n" if out and err else "") + err).strip()
	if merged:
		print(merged)
	if check and proc.returncode != 0:
		raise RuntimeError(
			f"Command failed ({proc.returncode}): {' '.join(resolved_cmd)}\n{merged}"
		)
	return proc.returncode, merged


def check_command_exists(name: str) -> None:
	if name == "npx" and os.name == "nt":
		if shutil.which("npx.cmd") or shutil.which("npx"):
			return
	if shutil.which(name) is None:
		raise RuntimeError(f"Required command not found in PATH: {name}")


def get_lock_path() -> Path:
	return Path.home() / ".agents" / ".skill-lock.json"


def load_installed_skills(lock_path: Path) -> Dict[str, dict]:
	if not lock_path.exists():
		return {}
	try:
		data = json.loads(lock_path.read_text(encoding="utf-8"))
		skills = data.get("skills", {})
		if isinstance(skills, dict):
			return skills
	except Exception:
		pass
	return {}


def print_final_skills(lock_path: Path) -> List[str]:
	skills = load_installed_skills(lock_path)
	names = sorted(skills.keys())
	print("\n=== Installed Skills ===")
	if not names:
		print("(none found in lock file)")
		return []
	for i, name in enumerate(names, start=1):
		print(f"{i:>2}. {name}")
	return names


def parse_skill_name_from_command(tokens: Sequence[str]) -> str | None:
	for i, token in enumerate(tokens):
		if token == "--skill" and i + 1 < len(tokens):
			return tokens[i + 1]
		if token.startswith("--skill="):
			return token.split("=", 1)[1].strip()
	return None


def is_full_npx_add_command(text: str) -> bool:
	return bool(re.match(r"^\s*npx\s+skills\s+add\b", text, re.IGNORECASE))


def looks_like_address(text: str) -> bool:
	value = text.strip()
	return value.startswith("git@") or value.startswith("http://") or value.startswith("https://")


def build_command_from_input(user_input: str) -> Tuple[List[str], str | None]:
	text = user_input.strip()
	if not text:
		raise RuntimeError("Empty input")

	if is_full_npx_add_command(text):
		tokens = shlex.split(text, posix=False)
		if "-g" not in tokens and "--global" not in tokens:
			tokens.append("-g")
		if "-y" not in tokens and "--yes" not in tokens:
			tokens.append("-y")
		skill_name = parse_skill_name_from_command(tokens)
		return tokens, skill_name

	if looks_like_address(text):
		# Address mode: default to global install and auto-confirm.
		return ["npx", "skills", "add", text, "-g", "-y"], None

	raise RuntimeError("Input must be a skill address or an 'npx skills add ...' command")


def main() -> int:
	configure_utf8_stdio()

	try:
		check_command_exists("npx")
	except RuntimeError as exc:
		print(f"[ERROR] {exc}")
		return 2

	print("请输入技能地址或者命令：", end="", flush=True)
	try:
		user_input = input()
	except EOFError:
		print("\n[ERROR] No input received.")
		return 1

	try:
		cmd, expected_skill = build_command_from_input(user_input)
		print(f"[INFO] Running: {' '.join(cmd)}")
		code, merged = run_cmd(cmd, check=False)
		# Some corporate/Windows environments miss CA chain for git HTTPS.
		if code != 0 and "SSL certificate" in merged and "unable to get local issuer certificate" in merged:
			print("[WARN] SSL certificate validation failed, retrying once with GIT_SSL_NO_VERIFY=true")
			code, _ = run_cmd(cmd, check=False, extra_env={"GIT_SSL_NO_VERIFY": "true"})
		if code != 0:
			print(f"[ERROR] Install command exited with code: {code}")
			return code

		installed_names = print_final_skills(get_lock_path())

		if expected_skill:
			if expected_skill in installed_names:
				print(f"\n[OK] Verification passed: '{expected_skill}' is installed.")
				return 0
			print(f"\n[ERROR] Verification failed: '{expected_skill}' not found in installed list.")
			return 1

		print("\n[OK] Installation command finished successfully.")
		return 0

	except Exception as exc:
		print(f"[ERROR] {exc}")
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
