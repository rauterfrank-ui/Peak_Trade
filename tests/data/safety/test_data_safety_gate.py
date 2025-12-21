"""
Tests für Data Safety Gate (IDEA-RISK-008)
==========================================

Testet die Safety-First Logik:
- Synthetische Daten dürfen NIEMALS für Live-Trading verwendet werden
- Synthetische Daten sind erlaubt für: Backtest, Research, Paper-Trading
- Reale und historische Daten sind grundsätzlich erlaubt
"""

from __future__ import annotations

import pytest

from src.data.safety import (
    DataSafetyContext,
    DataSafetyGate,
    DataSafetyResult,
    DataSafetyViolationError,
    DataSourceKind,
    DataUsageContextKind,
)


class TestDataSafetyGateBasics:
    """Basis-Tests für DataSafetyGate."""

    def test_enums_exist(self):
        """Enums sind korrekt definiert."""
        assert DataSourceKind.REAL.value == "real"
        assert DataSourceKind.HISTORICAL.value == "historical"
        assert DataSourceKind.SYNTHETIC_OFFLINE_RT.value == "synthetic_offline_rt"

        assert DataUsageContextKind.BACKTEST.value == "backtest"
        assert DataUsageContextKind.RESEARCH.value == "research"
        assert DataUsageContextKind.PAPER_TRADE.value == "paper_trade"
        assert DataUsageContextKind.LIVE_TRADE.value == "live_trade"

    def test_context_creation(self):
        """DataSafetyContext kann erstellt werden."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.REAL,
            usage=DataUsageContextKind.LIVE_TRADE,
        )
        assert ctx.source_kind == DataSourceKind.REAL
        assert ctx.usage == DataUsageContextKind.LIVE_TRADE
        assert ctx.run_id is None
        assert ctx.notes is None

    def test_context_with_optional_fields(self):
        """DataSafetyContext mit optionalen Feldern."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.BACKTEST,
            run_id="test-run-123",
            notes="Test-Run für Unit-Tests",
        )
        assert ctx.run_id == "test-run-123"
        assert ctx.notes == "Test-Run für Unit-Tests"

    def test_result_creation(self):
        """DataSafetyResult kann erstellt werden."""
        result = DataSafetyResult(
            allowed=True,
            reason="Test erlaubt",
        )
        assert result.allowed is True
        assert result.reason == "Test erlaubt"
        assert result.details is None

    def test_result_with_details(self):
        """DataSafetyResult mit Details."""
        result = DataSafetyResult(
            allowed=False,
            reason="Test nicht erlaubt",
            details={"rule": "TEST_RULE"},
        )
        assert result.allowed is False
        assert result.details == {"rule": "TEST_RULE"}


class TestSyntheticDataRules:
    """Tests für synthetische Daten-Regeln."""

    def test_synthetic_backtest_allowed(self):
        """Synthetische Daten für Backtest sind erlaubt."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.BACKTEST,
        )
        result = DataSafetyGate.check(ctx)
        assert result.allowed is True
        assert "erlaubt" in result.reason.lower()

    def test_synthetic_research_allowed(self):
        """Synthetische Daten für Research sind erlaubt."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.RESEARCH,
        )
        result = DataSafetyGate.check(ctx)
        assert result.allowed is True
        assert "erlaubt" in result.reason.lower()

    def test_synthetic_paper_trade_allowed(self):
        """Synthetische Daten für Paper-Trading sind erlaubt."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.PAPER_TRADE,
        )
        result = DataSafetyGate.check(ctx)
        assert result.allowed is True
        assert "erlaubt" in result.reason.lower()

    def test_synthetic_live_trade_blocked(self):
        """Synthetische Daten für Live-Trading sind VERBOTEN."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.LIVE_TRADE,
        )
        result = DataSafetyGate.check(ctx)
        assert result.allowed is False
        assert "verboten" in result.reason.lower() or "nicht erlaubt" in result.reason.lower()
        assert result.details is not None
        assert result.details["rule"] == "SYNTHETIC_LIVE_BLOCKED"


class TestRealDataRules:
    """Tests für reale Daten-Regeln."""

    @pytest.mark.parametrize(
        "usage",
        [
            DataUsageContextKind.BACKTEST,
            DataUsageContextKind.RESEARCH,
            DataUsageContextKind.PAPER_TRADE,
            DataUsageContextKind.LIVE_TRADE,
        ],
    )
    def test_real_data_always_allowed(self, usage: DataUsageContextKind):
        """Reale Daten sind in allen Kontexten erlaubt."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.REAL,
            usage=usage,
        )
        result = DataSafetyGate.check(ctx)
        assert result.allowed is True


class TestHistoricalDataRules:
    """Tests für historische Daten-Regeln."""

    @pytest.mark.parametrize(
        "usage",
        [
            DataUsageContextKind.BACKTEST,
            DataUsageContextKind.RESEARCH,
            DataUsageContextKind.PAPER_TRADE,
            DataUsageContextKind.LIVE_TRADE,
        ],
    )
    def test_historical_data_always_allowed(self, usage: DataUsageContextKind):
        """Historische Daten sind in allen Kontexten erlaubt."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.HISTORICAL,
            usage=usage,
        )
        result = DataSafetyGate.check(ctx)
        assert result.allowed is True


class TestEnsureAllowed:
    """Tests für ensure_allowed() Methode."""

    def test_ensure_allowed_passes_for_valid_context(self):
        """ensure_allowed() wirft keine Exception bei erlaubtem Kontext."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.BACKTEST,
        )
        # Sollte keine Exception werfen
        DataSafetyGate.ensure_allowed(ctx)

    def test_ensure_allowed_raises_for_invalid_context(self):
        """ensure_allowed() wirft DataSafetyViolationError bei verbotenem Kontext."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.LIVE_TRADE,
            run_id="test-run-456",
        )

        with pytest.raises(DataSafetyViolationError) as exc_info:
            DataSafetyGate.ensure_allowed(ctx)

        error = exc_info.value
        assert error.result.allowed is False
        assert error.context == ctx
        assert "SYNTHETIC_OFFLINE_RT" in str(error) or "synthetic" in str(error).lower()
        assert "LIVE_TRADE" in str(error) or "live" in str(error).lower()


class TestExceptionDetails:
    """Tests für Exception-Details."""

    def test_exception_contains_result(self):
        """DataSafetyViolationError enthält das Result-Objekt."""
        result = DataSafetyResult(
            allowed=False,
            reason="Test-Verletzung",
            details={"test_key": "test_value"},
        )
        error = DataSafetyViolationError(result=result)

        assert error.result == result
        assert error.result.reason == "Test-Verletzung"
        assert "Test-Verletzung" in str(error)

    def test_exception_contains_context(self):
        """DataSafetyViolationError enthält den Kontext."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.LIVE_TRADE,
        )
        result = DataSafetyResult(
            allowed=False,
            reason="Verboten",
        )
        error = DataSafetyViolationError(result=result, context=ctx)

        assert error.context == ctx
        assert "synthetic_offline_rt" in str(error)
        assert "live_trade" in str(error)

    def test_exception_message_format(self):
        """Exception-Message hat korrektes Format."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.SYNTHETIC_OFFLINE_RT,
            usage=DataUsageContextKind.LIVE_TRADE,
        )

        with pytest.raises(DataSafetyViolationError) as exc_info:
            DataSafetyGate.ensure_allowed(ctx)

        error_message = str(exc_info.value)
        assert "DataSafetyViolation" in error_message


class TestEdgeCases:
    """Tests für Randfälle."""

    def test_frozen_dataclasses(self):
        """DataSafetyContext und DataSafetyResult sind immutable."""
        ctx = DataSafetyContext(
            source_kind=DataSourceKind.REAL,
            usage=DataUsageContextKind.BACKTEST,
        )

        with pytest.raises(AttributeError):
            ctx.source_kind = DataSourceKind.SYNTHETIC_OFFLINE_RT  # type: ignore

        result = DataSafetyResult(allowed=True, reason="Test")
        with pytest.raises(AttributeError):
            result.allowed = False  # type: ignore

    def test_all_combinations_have_defined_behavior(self):
        """Alle Kombinationen von source_kind und usage haben definiertes Verhalten."""
        for source in DataSourceKind:
            for usage in DataUsageContextKind:
                ctx = DataSafetyContext(source_kind=source, usage=usage)
                result = DataSafetyGate.check(ctx)

                # Result sollte immer gültig sein
                assert isinstance(result.allowed, bool)
                assert isinstance(result.reason, str)
                assert len(result.reason) > 0

                # Entweder erlaubt oder blockiert
                if result.allowed:
                    # ensure_allowed sollte nicht werfen
                    DataSafetyGate.ensure_allowed(ctx)
                else:
                    # ensure_allowed sollte werfen
                    with pytest.raises(DataSafetyViolationError):
                        DataSafetyGate.ensure_allowed(ctx)
