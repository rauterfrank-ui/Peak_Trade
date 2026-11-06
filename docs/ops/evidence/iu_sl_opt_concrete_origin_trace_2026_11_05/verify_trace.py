"""Verify retained original values and source bindings; never run product code."""

from pathlib import Path
import hashlib
import json
import math
import statistics
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(folder):
    repo = Path(
        subprocess.check_output(
            ["git", "-C", str(folder), "rev-parse", "--show-toplevel"], text=True
        ).strip()
    )
    trace = json.loads((folder / "trace.json").read_text())
    manifest = json.loads((folder / "manifest.json").read_text())
    for row in manifest["files"]:
        assert sha((folder / row["path"]).read_bytes()) == row["sha256"], row["path"]
    assert {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()} == {
        row["path"] for row in manifest["files"]
    } | {"manifest.json"}
    for rel, row in trace["bound_sources"].items():
        raw = subprocess.check_output(
            ["git", "-C", str(repo), "show", trace["source_head"] + ":" + rel]
        )
        assert sha(raw) == row["sha256"], rel

    originals = {}
    for row in trace["original_artifacts"]:
        saved = json.loads((repo / row["path"]).read_text())
        raw = saved["original_utf8"].encode()
        assert sha(raw) == saved["sha256"] == row["sha256"]
        originals[Path(row["path"]).stem] = json.loads(raw)

    measurement = originals["mi_original_measurement"]["measurement"]
    realized = math.log(measurement["end_price"] / measurement["start_price"])
    ack = originals["mi_original_ack"]["numeric_readback"]
    forecast = originals["mi_original_durable_triad"]["forecast_evidence"]
    assert forecast["probabilistic_payload"]["mean_return"] == trace["mi"]["forecast_mean"]
    assert realized == ack["realized_return"] == trace["mi"]["realized_log_return"]
    assert realized - trace["mi"]["forecast_mean"] == ack["error"]
    assert trace["mi"]["ddo_next_cycle_label"] == "UNKNOWN"
    for label, observation in zip(("first", "second"), trace["e6_actual_executions"]):
        packet = originals["e6_" + label + "_original_packet"]
        run = packet["measurement_receipt"]["runs"][0]
        equity = [p["value"] for p in run["equity"]]
        returns = [v / p - 1 for p, v in zip(equity, equity[1:])]
        sharpe = statistics.mean(returns) / statistics.stdev(returns)
        assert abs(sharpe - run["statistics"]["sharpe"]["value"]) < 1e-15
        assert sharpe == observation["full_sharpe_recomputed"]
        assert run["engine_signal_digest"] == run["mv2_signal_digest"]
        assert run["engine_signal_digest"] != run["strategy_provenance"]["engine_signal_digest"]
    second = json.loads(originals["e6_second_original_packet"]["execution_utf8"])
    assert second["search_record"]["input_lineage"]["meta_learning_identity"] is None
    candidate = next(
        c
        for c in second["search_record"]["candidates"]
        if c["parameter_region"]["slow_window"] == 50
    )
    assert candidate["status"] == "REJECTED_DUPLICATE_WITHOUT_RETEST"
    started = originals["e6_second_original_started"]["body"]
    assert (
        started["feedback"]["meta_input_binding"]["meta_learning_record"]["research_proposals"]
        == []
    )
    assert [
        c["selected_slow_window"] for c in trace["same_candidate_meta_signal_intervention"]
    ] == [
        100,
        50,
        50,
    ]
    index = json.loads(
        (folder.parent / "iu_sl_opt_understanding_resolution_2026_11_05.json").read_text()
    )
    assert sha((repo / index["document"]).read_bytes()) == index["document_sha256"]
    assert sha((folder / "trace.json").read_bytes()) == index["trace_sha256"]
    return {
        "result": "PASS_RETAINED_VALUE_AND_SOURCE_READBACK",
        "source_head": trace["source_head"],
        "source_files": len(trace["bound_sources"]),
        "original_artifacts": len(originals),
        "realized_return": realized,
        "forecast_error": ack["error"],
        "E6_choice_cause": "DUPLICATE_NOT_META",
        "product_modules_imported": False,
        "engine_or_training_runs": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(Path(__file__).resolve().parent), ensure_ascii=False, indent=2))
