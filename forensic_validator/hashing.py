"""Bütünlük doğrulama: dosya/imaj hash hesaplama ve karşılaştırma."""

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MiB — büyük disk imajlarını belleğe yüklemeden okumak için

SUPPORTED_ALGOS = ("md5", "sha1", "sha256", "sha512")


def compute_hash(path: str, algo: str = "sha256") -> str:
    if algo not in SUPPORTED_ALGOS:
        raise ValueError(f"Desteklenmeyen algoritma: {algo}. Seçenekler: {SUPPORTED_ALGOS}")

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

    hasher = hashlib.new(algo)
    with p.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def compare_files(path_a: str, path_b: str, algo: str = "sha256") -> dict:
    hash_a = compute_hash(path_a, algo)
    hash_b = compute_hash(path_b, algo)
    return {
        "algo": algo,
        "path_a": path_a,
        "path_b": path_b,
        "hash_a": hash_a,
        "hash_b": hash_b,
        "match": hash_a == hash_b,
    }


def verify_file(path: str, expected_hash: str, algo: str = "sha256") -> dict:
    actual = compute_hash(path, algo)
    return {
        "algo": algo,
        "path": path,
        "expected": expected_hash.lower().strip(),
        "actual": actual,
        "match": actual == expected_hash.lower().strip(),
    }
