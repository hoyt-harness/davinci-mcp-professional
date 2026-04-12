"""
Security-focused test suite for DaVinci MCP Professional.

This module contains tests specifically designed to verify security aspects
of the application, including dependency security, file permissions, and
potential vulnerability detection.
"""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Directory names that must always be excluded from file scans.
_SCAN_EXCLUDE_DIRS: set[str] = {".venv", "lib", "dist", "build", ".git", "node_modules"}


def _excluded(path: Path) -> bool:
    """Return True if any component of *path* is in the exclude set."""
    return bool(_SCAN_EXCLUDE_DIRS & set(path.parts))


class TestSecurity:
    """Security-focused test cases."""

    def test_no_secrets_in_codebase(self):
        """Check for potential hardcoded secrets in source code."""
        project_root = Path(__file__).parent.parent
        python_files = [
            p for p in project_root.rglob("*.py")
            if not _excluded(p) and "test_" not in p.name
        ]

        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            "password=",
            "api_key=",
            "secret=",
            "token=",
            "aws_access_key",
            "private_key=",
        ]

        violations = []
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8").lower()
                for pattern in secret_patterns:
                    if pattern in content:
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if pattern in line and not line.strip().startswith("#"):
                                violations.append(f"{py_file}:{i+1} - {line.strip()}")
            except UnicodeDecodeError:
                continue

        if violations:
            pytest.fail("Potential hardcoded secrets found:\n" + "\n".join(violations))

    def test_dependencies_security(self):
        """Check for known vulnerabilities in dependencies using safety."""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

            if result.returncode != 0:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    if vulnerabilities:
                        vuln_summary = []
                        for vuln in vulnerabilities:
                            vuln_summary.append(
                                f"Package: {vuln.get('package', 'Unknown')} "
                                f"Version: {vuln.get('installed_version', 'Unknown')} "
                                f"Vulnerability: {vuln.get('vulnerability_id', 'Unknown')}"
                            )
                        pytest.fail(
                            "Security vulnerabilities found:\n" + "\n".join(vuln_summary)
                        )
                except json.JSONDecodeError:
                    if "vulnerabilities found" in result.stdout.lower():
                        pytest.fail(f"Security vulnerabilities detected: {result.stdout}")

        except FileNotFoundError:
            pytest.skip("Safety tool not installed. Run: uv sync")

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="POSIX file permissions are not applicable on Windows (NTFS uses ACLs)",
    )
    def test_file_permissions(self):
        """Ensure sensitive files have appropriate permissions (POSIX only)."""
        project_root = Path(__file__).parent.parent

        # Files that should not be world-readable.
        # *config*.json is intentionally narrow: template files that are
        # explicitly public (e.g. claude_desktop_config_template.json) are
        # excluded via the allowlist below.
        sensitive_patterns = [
            ".env*",
            "*secret*",
            "*.key",
            "*.pem",
            "credentials*",
        ]

        # Known-safe files that match sensitive patterns but are intentionally
        # public (e.g. documentation templates).
        allowlist: set[str] = {
            "claude_desktop_config_template.json",
        }

        violations = []
        for pattern in sensitive_patterns:
            for file_path in project_root.rglob(pattern):
                if not file_path.is_file():
                    continue
                if _excluded(file_path):
                    continue
                if file_path.name in allowlist:
                    continue
                if file_path.stat().st_mode & stat.S_IROTH:
                    violations.append(f"{file_path} is world-readable")

        if violations:
            pytest.fail("Insecure file permissions found:\n" + "\n".join(violations))

    def test_import_security(self):
        """Check for potentially dangerous imports."""
        project_root = Path(__file__).parent.parent
        python_files = [
            p for p in project_root.rglob("*.py")
            if not _excluded(p) and "test_" not in p.name
        ]

        dangerous_imports = [
            "eval(",
            "exec(",
            "compile(",
            "__import__(",
            "subprocess.call(",
            "os.system(",
            "pickle.loads(",
            "marshal.loads(",
        ]

        violations = []
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    for dangerous in dangerous_imports:
                        if dangerous in line and not line.strip().startswith("#"):
                            violations.append(
                                f"{py_file}:{i+1} - Potentially dangerous: {line.strip()}"
                            )
            except UnicodeDecodeError:
                continue

        # Warning only — some uses may be legitimate
        if violations:
            print("⚠️  Potentially dangerous imports found (review required):")
            for violation in violations:
                print(f"   {violation}")

    def test_environment_variables(self):
        """Check for insecure environment variable handling."""
        sensitive_env_vars = [
            "AWS_SECRET_ACCESS_KEY",
            "DATABASE_PASSWORD",
            "API_SECRET",
            "PRIVATE_KEY",
            "TOKEN",
        ]
        exposed_vars = [v for v in sensitive_env_vars if os.getenv(v)]
        if exposed_vars:
            print(f"⚠️  Sensitive environment variables detected: {', '.join(exposed_vars)}")
            print("Ensure these are properly secured in production.")

    def test_configuration_security(self):
        """Check configuration files for security issues."""
        project_root = Path(__file__).parent.parent
        config_files = [
            f
            for pattern in ["*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.conf"]
            for f in project_root.rglob(pattern)
            if not _excluded(f)
        ]

        violations = []
        for config_file in config_files:
            try:
                content = config_file.read_text(encoding="utf-8").lower()
                if not any(
                    s in content for s in ["password", "secret", "token", "key", "credential"]
                ):
                    continue
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "=" not in line and ":" not in line:
                        continue
                    if not any(s in line for s in ["password", "secret", "token", "key"]):
                        continue
                    parts = line.split("=" if "=" in line else ":")
                    if len(parts) > 1 and parts[1].strip():
                        violations.append(
                            f"{config_file}:{i+1} - Potential secret: {line.strip()}"
                        )
            except UnicodeDecodeError:
                continue

        if violations:
            print("⚠️  Potential secrets in configuration files:")
            for violation in violations:
                print(f"   {violation}")


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_path_traversal_protection(self) -> None:
        """Test protection against path traversal attacks."""
        print(
            "📝 Path traversal protection tests should be implemented "
            "based on your file handling logic"
        )

    def test_command_injection_protection(self) -> None:
        """Test protection against command injection."""
        print(
            "📝 Command injection protection tests should be implemented "
            "if executing system commands"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
