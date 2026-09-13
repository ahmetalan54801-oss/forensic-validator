"""NIST CFTT tarzı araç doğrulama: bilinen girdi + beklenen çıktı ile test.

Bir test suite'i (YAML), doğrulanacak adli aracı belirli komutlarla çalıştırır
ve çıktının (exit code, stdout/stderr içeriği, üretilen dosyanın hash'i)
beklentilerle eşleşip eşleşmediğini kontrol eder.
"""

import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .hashing import compute_hash


@dataclass
class CaseResult:
    name: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None


def load_suite(suite_path: str) -> dict:
    with open(suite_path, "r", encoding="utf-8") as f:
        suite = yaml.safe_load(f)
    if not suite or "cases" not in suite:
        raise ValueError("Test suite dosyasında 'cases' listesi bulunamadı")
    return suite


def _format(value: str, variables: dict) -> str:
    return value.format(**variables)


def run_case(case: dict, base_dir: Path) -> CaseResult:
    name = case.get("name", "isimsiz test")
    variables = case.get("vars", {})
    result = CaseResult(name=name, passed=True)

    try:
        command = _format(case["command"], variables)
        proc = subprocess.run(
            shlex.split(command),
            cwd=base_dir,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=case.get("timeout", 60),
        )
    except Exception as exc:  # noqa: BLE001 - test aracının kendi hatasını da raporlamak istiyoruz
        result.passed = False
        result.failures.append(f"Komut çalıştırılamadı: {exc}")
        return result

    result.stdout = proc.stdout
    result.stderr = proc.stderr
    result.exit_code = proc.returncode

    expect = case.get("expect", {})

    if "exit_code" in expect and proc.returncode != expect["exit_code"]:
        result.passed = False
        result.failures.append(f"exit_code beklenen={expect['exit_code']} gerçek={proc.returncode}")

    if "stdout_contains" in expect and expect["stdout_contains"] not in proc.stdout:
        result.passed = False
        result.failures.append(f"stdout içinde bulunamadı: {expect['stdout_contains']!r}")

    if "stderr_contains" in expect and expect["stderr_contains"] not in proc.stderr:
        result.passed = False
        result.failures.append(f"stderr içinde bulunamadı: {expect['stderr_contains']!r}")

    if "file_hash" in expect:
        fh = expect["file_hash"]
        path = base_dir / _format(fh["path"], variables)
        algo = fh.get("algo", "sha256")
        expected = fh["expected"]
        try:
            actual = compute_hash(str(path), algo)
        except FileNotFoundError:
            result.passed = False
            result.failures.append(f"beklenen çıktı dosyası yok: {path}")
        else:
            if actual.lower() != expected.lower():
                result.passed = False
                result.failures.append(f"{path} hash uyuşmuyor: beklenen={expected} gerçek={actual}")

    if "files_match" in expect:
        fm = expect["files_match"]
        path_a = base_dir / _format(fm["a"], variables)
        path_b = base_dir / _format(fm["b"], variables)
        algo = fm.get("algo", "sha256")
        try:
            hash_a = compute_hash(str(path_a), algo)
            hash_b = compute_hash(str(path_b), algo)
        except FileNotFoundError as exc:
            result.passed = False
            result.failures.append(f"dosya bulunamadı: {exc}")
        else:
            if hash_a != hash_b:
                result.passed = False
                result.failures.append(f"{path_a} ve {path_b} hash'leri farklı ({algo})")

    return result


def run_suite(suite_path: str) -> list[CaseResult]:
    suite = load_suite(suite_path)
    base_dir = Path(suite_path).resolve().parent
    return [run_case(case, base_dir) for case in suite["cases"]]


def render_report(suite_name: str, results: list[CaseResult]) -> str:
    lines = [f"# Test Raporu: {suite_name}", ""]
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    lines.append(f"**Sonuç: {passed}/{total} test başarılı**")
    lines.append("")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"## [{status}] {r.name}")
        if r.exit_code is not None:
            lines.append(f"- exit_code: {r.exit_code}")
        if r.failures:
            lines.append("- Hatalar:")
            for f in r.failures:
                lines.append(f"  - {f}")
        lines.append("")
    return "\n".join(lines)
