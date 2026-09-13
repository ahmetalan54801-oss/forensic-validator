import argparse
import hashlib
import sys
from pathlib import Path

from . import hashing, ledger, testing


def cmd_hash_compute(args):
    digest = hashing.compute_hash(args.file, args.algo)
    print(f"{digest}  {args.file}")


def cmd_hash_compare(args):
    result = hashing.compare_files(args.file_a, args.file_b, args.algo)
    print(f"[{args.algo}] {result['path_a']} = {result['hash_a']}")
    print(f"[{args.algo}] {result['path_b']} = {result['hash_b']}")
    print("EŞLEŞTİ" if result["match"] else "EŞLEŞMEDİ")
    sys.exit(0 if result["match"] else 1)


def cmd_hash_verify(args):
    result = hashing.verify_file(args.file, args.expected, args.algo)
    print(f"[{args.algo}] beklenen : {result['expected']}")
    print(f"[{args.algo}] gerçek   : {result['actual']}")
    print("DOĞRULANDI" if result["match"] else "DOĞRULANAMADI")
    sys.exit(0 if result["match"] else 1)


def cmd_testsuite_run(args):
    results = testing.run_suite(args.suite)
    report = testing.render_report(args.suite, results)
    print(report)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nRapor kaydedildi: {args.report}", file=sys.stderr)

    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed

    if args.ledger:
        report_hash = hashlib.sha256(report.encode("utf-8")).hexdigest()
        entry = ledger.add_entry(
            args.ledger,
            actor=args.actor,
            action=f"testsuite çalıştırıldı: {Path(args.suite).name}",
            details=f"sonuc={passed}/{len(results)} rapor_sha256={report_hash}",
        )
        print(f"\nLedger kaydı eklendi: {entry['entry_hash'][:12]}... ({args.ledger})", file=sys.stderr)

    sys.exit(1 if failed else 0)


def cmd_ledger_add(args):
    entry = ledger.add_entry(args.file, args.actor, args.action, args.details or "")
    print(f"Kayıt eklendi: {entry['entry_hash'][:12]}... ({entry['timestamp']})")


def cmd_ledger_verify(args):
    result = ledger.verify_chain(args.file)
    if result["valid"]:
        print(f"Zincir sağlam. {result['entry_count']} kayıt doğrulandı.")
        sys.exit(0)
    else:
        print(f"ZİNCİR BOZUK: kayıt #{result['broken_at']} — {result['reason']}")
        sys.exit(1)


def cmd_ledger_show(args):
    for i, entry in enumerate(ledger.list_entries(args.file)):
        print(f"[{i}] {entry['timestamp']} | {entry['actor']} | {entry['action']} | {entry['details']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forensic-validator", description="Adli araç ve yöntem doğrulama aracı")
    sub = parser.add_subparsers(dest="command", required=True)

    hash_p = sub.add_parser("hash", help="Dosya bütünlüğü doğrulama")
    hash_sub = hash_p.add_subparsers(dest="hash_command", required=True)

    p = hash_sub.add_parser("compute", help="Dosyanın hash'ini hesapla")
    p.add_argument("file")
    p.add_argument("--algo", default="sha256", choices=hashing.SUPPORTED_ALGOS)
    p.set_defaults(func=cmd_hash_compute)

    p = hash_sub.add_parser("compare", help="İki dosyayı hash ile karşılaştır")
    p.add_argument("file_a")
    p.add_argument("file_b")
    p.add_argument("--algo", default="sha256", choices=hashing.SUPPORTED_ALGOS)
    p.set_defaults(func=cmd_hash_compare)

    p = hash_sub.add_parser("verify", help="Dosyayı beklenen hash ile doğrula")
    p.add_argument("file")
    p.add_argument("expected")
    p.add_argument("--algo", default="sha256", choices=hashing.SUPPORTED_ALGOS)
    p.set_defaults(func=cmd_hash_verify)

    testsuite_p = sub.add_parser("testsuite", help="Araç doğrulama test suite'i çalıştır")
    testsuite_sub = testsuite_p.add_subparsers(dest="testsuite_command", required=True)

    p = testsuite_sub.add_parser("run", help="Bir test suite'ini çalıştır")
    p.add_argument("suite", help="YAML test suite dosyası")
    p.add_argument("--report", help="Sonucu Markdown olarak bu dosyaya yaz")
    p.add_argument("--ledger", help="Sonucu bu zincir-i emanet defterine de kaydet (jsonl)")
    p.add_argument("--actor", default="system", help="Ledger kaydında görünecek işlemi yapan kişi/sistem")
    p.set_defaults(func=cmd_testsuite_run)

    ledger_p = sub.add_parser("ledger", help="Zincir-i emanet (chain-of-custody) defteri")
    ledger_sub = ledger_p.add_subparsers(dest="ledger_command", required=True)

    p = ledger_sub.add_parser("add", help="Deftere yeni kayıt ekle")
    p.add_argument("--file", required=True, help="Defter dosyası (jsonl)")
    p.add_argument("--actor", required=True, help="İşlemi yapan kişi")
    p.add_argument("--action", required=True, help="Yapılan işlem")
    p.add_argument("--details", default="", help="Ek açıklama")
    p.set_defaults(func=cmd_ledger_add)

    p = ledger_sub.add_parser("verify", help="Defter zincirinin bütünlüğünü doğrula")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_ledger_verify)

    p = ledger_sub.add_parser("show", help="Defterdeki kayıtları listele")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_ledger_show)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
