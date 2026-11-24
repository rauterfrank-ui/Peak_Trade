"""Read the Slot 3 EEA Demo account once, independent of a trading session."""

import argparse
from datetime import datetime, timezone
import getpass
import json
import subprocess
import sys
import warnings
from urllib.parse import urlencode

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_budget_reconciliation_host_v1 import validate_btc_demo_coverage_v1
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    format_okx_access_timestamp_iso_ms_v1,
    sign_okx_request_v1,
)


def account_reader(api_key, secret, passphrase):
    """Limit signing to the four exact account queries used by the coverage reader."""
    endpoints = {
        demo._CONFIG,
        demo._BALANCE + "?" + urlencode({"ccy": "USD,USDC"}),
        demo._INSTRUMENTS + "?" + urlencode({"instType": "FUTURES", "instId": demo._NATIVE}),
        demo._FEE + "?" + urlencode({"instType": "FUTURES", "instFamily": demo._FAMILY}),
    }

    def sign_get(endpoint):
        if endpoint not in endpoints:
            raise ValueError("BTC_DEMO_ACCOUNT_QUERY_OUT_OF_SCOPE")
        timestamp = format_okx_access_timestamp_iso_ms_v1()
        return {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-PASSPHRASE": passphrase,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-SIGN": sign_okx_request_v1(
                secret=secret, timestamp=timestamp, method="GET", request_path=endpoint, body=""
            ),
        }

    return demo.OkxEeaDemoReadsV1(secret_reference=demo._DEMO.secret_reference, sign_get=sign_get)


def inspect_account(reads, expected_uid, clock):
    report = demo.read_btc_demo_coverage_v2(reads=reads, expected_uid=expected_uid)
    validate_btc_demo_coverage_v1(report, account=expected_uid, now=clock())
    rows = {r["path"]: r["payload"]["data"][0] for r in report["source_observations"]}
    account = rows[demo._CONFIG]
    settlement = account.get("settleCcy") or None
    allowed = account.get("settleCcyList")
    if settlement is not None and not (
        isinstance(settlement, str)
        and settlement.isascii()
        and settlement.isalpha()
        and settlement.isupper()
        and len(settlement) <= 10
    ):
        raise ValueError("BTC_DEMO_ACCOUNT_SETTLEMENT_INVALID")
    instrument = rows[demo._INSTRUMENTS]
    fee = next(f for f in rows[demo._FEE]["feeGroup"] if f["groupId"] == instrument["groupId"])
    return {
        "key_permissions": account.get("perm") or None,
        "instrument": demo._NATIVE,
        "observed_at": report["coverage_observed_at"],
        "futures_account_mode": account.get("acctLv") == "2" if account.get("acctLv") else None,
        "one_way_position_mode": report["position_mode"] == "net_mode",
        "account_usd_m_settlement_currency": settlement,
        "usdc_in_account_settlement_choices": "USDC" in allowed
        if isinstance(allowed, list)
        else None,
        "private_instrument_settlement_currency": report["venue_settlement_currency"],
        "available_equity_usdc": report["available_equity"].get("USDC"),
        "declared_budget_usdc": report["budget_usdc"],
        "available_equity_covers_cap": report["available_usdc_covers_declared_budget"],
        "public_index_value_of_cap_usd": report["budget_value_usd"],
        "maker_fee_rate_signed": str(demo._money(fee["maker"])) if fee.get("maker") else None,
        "taker_fee_rate_signed": report["taker_fee_rate_signed"],
        "sizing_verified": False,
        "trading_authority": report["trading_authority"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Einmalige Leseprüfung für Slot 3 im OKX-EEA-Demokonto."
    )
    parser.add_argument("--keychain-service", help="Bestehenden macOS-Schlüsselbunddienst lesen")
    parser.add_argument("--demo-uid", help="Erwartete UID des Demokontos")
    parser.add_argument("--lesen", action="store_true", help="Demokonto einmal lesend abfragen")
    args = parser.parse_args()
    if not args.lesen:
        parser.print_help()
        return 0
    if not args.keychain_service and not sys.stdin.isatty():
        parser.exit(2, "Für die verdeckte Eingabe ist ein lokales Terminal erforderlich.\n")
    try:
        if args.keychain_service:
            uid = args.demo_uid or ""
            fields = []
            for field in ("api-key", "secret", "passphrase"):
                value = subprocess.run(
                    [
                        "/usr/bin/security",
                        "find-generic-password",
                        "-s",
                        args.keychain_service,
                        "-a",
                        field,
                        "-w",
                    ],
                    capture_output=True,
                    check=True,
                    timeout=60,
                )
                fields.append(value.stdout.decode().rstrip("\n"))
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                uid = args.demo_uid or getpass.getpass("Erwartete UID des Demokontos: ").strip()
                fields = [
                    getpass.getpass(prompt)
                    for prompt in ("Demo-API-Key: ", "Demo-API-Secret: ", "Demo-API-Passphrase: ")
                ]
        if not uid.isascii() or not uid.isdecimal():
            raise ValueError("Ungültige UID")
        if not all(fields):
            raise ValueError("Unvollständige Eingabe")
        result = inspect_account(
            account_reader(*fields), uid, lambda: datetime.now(timezone.utc).timestamp()
        )
    except (
        subprocess.SubprocessError,
        EOFError,
        OSError,
        ArithmeticError,
        ValueError,
        KeyError,
        TypeError,
        getpass.GetPassWarning,
    ) as exc:
        # Exception messages of network and parsing libraries can contain private response data.
        print(f"Demo-Leseprüfung ohne Ergebnis ({type(exc).__name__}).", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
