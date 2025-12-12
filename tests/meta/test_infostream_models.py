"""
Tests für InfoStream v1 Core Models.

Testet Roundtrip-Serialisierung und grundlegende Funktionalität der
drei Kern-Datenstrukturen: IntelEvent, InfoPacket, LearningSnippet.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.meta.infostream import IntelEvent, InfoPacket, LearningSnippet


class TestIntelEvent:
    """Tests für IntelEvent."""

    def test_roundtrip_basic(self) -> None:
        """Test: Einfacher Roundtrip mit to_dict/from_dict."""
        event = IntelEvent(
            source="GLOBAL_MACRO",
            topic="Test-Event",
            summary="Kurze Testbeschreibung.",
            importance=4,
            tags=["macro", "test"],
            payload={"foo": "bar"},
        )

        data = event.to_dict()
        cloned = IntelEvent.from_dict(data)

        assert cloned.event_id == event.event_id
        assert cloned.source == "GLOBAL_MACRO"
        assert cloned.topic == "Test-Event"
        assert cloned.summary == "Kurze Testbeschreibung."
        assert cloned.importance == 4
        assert cloned.tags == ["macro", "test"]
        assert cloned.payload["foo"] == "bar"

    def test_auto_generated_id(self) -> None:
        """Test: event_id wird automatisch generiert."""
        event = IntelEvent(source="TEST")
        assert event.event_id.startswith("intel_")
        assert len(event.event_id) > 10

    def test_auto_generated_timestamp(self) -> None:
        """Test: created_at wird automatisch auf UTC gesetzt."""
        event = IntelEvent(source="TEST")
        assert event.created_at.tzinfo is not None
        assert event.created_at.tzinfo == timezone.utc

    def test_json_serializable(self) -> None:
        """Test: to_dict() Ergebnis ist JSON-serialisierbar."""
        event = IntelEvent(
            source="TEST",
            topic="JSON Test",
            tags=["a", "b"],
            payload={"nested": {"value": 123}},
        )

        data = event.to_dict()
        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert parsed["source"] == "TEST"
        assert parsed["payload"]["nested"]["value"] == 123

    def test_default_values(self) -> None:
        """Test: Default-Werte werden korrekt gesetzt."""
        event = IntelEvent()

        assert event.source == "unknown"
        assert event.topic == ""
        assert event.summary == ""
        assert event.importance == 3
        assert event.tags == []
        assert event.payload == {}


class TestInfoPacket:
    """Tests für InfoPacket."""

    def test_roundtrip_basic(self) -> None:
        """Test: Einfacher Roundtrip mit eingebettetem IntelEvent."""
        event = IntelEvent(source="TEST_SOURCE", topic="Test Topic")
        packet = InfoPacket(
            intel_event=event,
            channel="TEST_CHANNEL",
            status="new",
            meta={"run_id": "abc123"},
        )

        data = packet.to_dict()
        cloned = InfoPacket.from_dict(data)

        assert cloned.packet_id == packet.packet_id
        assert cloned.intel_event.source == "TEST_SOURCE"
        assert cloned.intel_event.topic == "Test Topic"
        assert cloned.channel == "TEST_CHANNEL"
        assert cloned.status == "new"
        assert cloned.meta["run_id"] == "abc123"

    def test_auto_generated_packet_id(self) -> None:
        """Test: packet_id wird automatisch generiert."""
        packet = InfoPacket()
        assert packet.packet_id.startswith("packet_")

    def test_nested_intel_event_serialization(self) -> None:
        """Test: Eingebettetes IntelEvent wird korrekt serialisiert."""
        event = IntelEvent(
            source="MACRO",
            topic="Nested Test",
            importance=5,
            tags=["nested"],
        )
        packet = InfoPacket(intel_event=event)

        data = packet.to_dict()

        assert "intel_event" in data
        assert data["intel_event"]["source"] == "MACRO"
        assert data["intel_event"]["importance"] == 5

    def test_status_values(self) -> None:
        """Test: Verschiedene Status-Werte werden korrekt verarbeitet."""
        for status in ["new", "in_review", "processed"]:
            packet = InfoPacket(status=status)  # type: ignore[arg-type]
            data = packet.to_dict()
            cloned = InfoPacket.from_dict(data)
            assert cloned.status == status

    def test_json_serializable(self) -> None:
        """Test: Komplettes InfoPacket ist JSON-serialisierbar."""
        event = IntelEvent(source="JSON_TEST", payload={"key": [1, 2, 3]})
        packet = InfoPacket(
            intel_event=event,
            channel="JSON_CHANNEL",
            meta={"complex": {"nested": True}},
        )

        json_str = json.dumps(packet.to_dict())
        parsed = json.loads(json_str)

        assert parsed["channel"] == "JSON_CHANNEL"
        assert parsed["intel_event"]["payload"]["key"] == [1, 2, 3]


class TestLearningSnippet:
    """Tests für LearningSnippet."""

    def test_roundtrip_basic(self) -> None:
        """Test: Einfacher Roundtrip mit allen Feldern."""
        snippet = LearningSnippet(
            source_packet_id="packet_123",
            topic="TestTopic",
            content="Some important learning content.",
            tags=["a", "b"],
            quality_score=0.9,
            extra={"model": "o3-deep-research"},
        )

        data = snippet.to_dict()
        cloned = LearningSnippet.from_dict(data)

        assert cloned.snippet_id == snippet.snippet_id
        assert cloned.source_packet_id == "packet_123"
        assert cloned.topic == "TestTopic"
        assert cloned.content == "Some important learning content."
        assert cloned.tags == ["a", "b"]
        assert cloned.quality_score == 0.9
        assert cloned.extra["model"] == "o3-deep-research"

    def test_auto_generated_snippet_id(self) -> None:
        """Test: snippet_id wird automatisch generiert."""
        snippet = LearningSnippet()
        assert snippet.snippet_id.startswith("learn_")

    def test_optional_quality_score(self) -> None:
        """Test: quality_score ist optional und kann None sein."""
        snippet = LearningSnippet(topic="Test")
        assert snippet.quality_score is None

        data = snippet.to_dict()
        cloned = LearningSnippet.from_dict(data)
        assert cloned.quality_score is None

    def test_quality_score_roundtrip(self) -> None:
        """Test: quality_score wird korrekt serialisiert."""
        snippet = LearningSnippet(quality_score=0.75)

        data = snippet.to_dict()
        cloned = LearningSnippet.from_dict(data)

        assert cloned.quality_score == 0.75

    def test_json_serializable(self) -> None:
        """Test: LearningSnippet ist JSON-serialisierbar."""
        snippet = LearningSnippet(
            topic="JSON Test",
            content="Test content",
            extra={"sources": ["url1", "url2"]},
        )

        json_str = json.dumps(snippet.to_dict())
        parsed = json.loads(json_str)

        assert parsed["topic"] == "JSON Test"
        assert parsed["extra"]["sources"] == ["url1", "url2"]


class TestIntegration:
    """Integrationstests für den kompletten InfoStream-Flow."""

    def test_full_flow_event_to_packet_to_snippet(self) -> None:
        """Test: Kompletter Flow von Event über Packet zu Snippet."""
        # 1. Event erstellen
        event = IntelEvent(
            source="GLOBAL_MACRO",
            topic="Fed Zinsentscheidung",
            summary="Fed senkt Zinsen um 25bp auf 3.5%.",
            importance=4,
            tags=["macro", "fed", "rates"],
            payload={"rate": 3.5, "change": -0.25},
        )

        # 2. In Packet packen
        packet = InfoPacket(
            intel_event=event,
            channel="GLOBAL_MACRO_DAILY",
            status="new",
            meta={"analyst": "GlobalMacroSpecialist"},
        )

        # 3. "KI-Evaluator" erzeugt Snippet
        snippet = LearningSnippet(
            source_packet_id=packet.packet_id,
            topic="Geldpolitik / Fed",
            content="Die Fed hat am 10.12.2025 die Zinsen um 25bp gesenkt. "
            "Dies war die dritte Senkung des Jahres. "
            "Powell signalisiert Pause für 2026.",
            tags=["macro", "fed", "learning"],
            quality_score=0.85,
            extra={"model": "gpt-4o"},
        )

        # 4. Alles serialisieren und wieder laden
        packet_data = packet.to_dict()
        snippet_data = snippet.to_dict()

        packet_restored = InfoPacket.from_dict(packet_data)
        snippet_restored = LearningSnippet.from_dict(snippet_data)

        # 5. Verifikation
        assert packet_restored.intel_event.source == "GLOBAL_MACRO"
        assert packet_restored.intel_event.payload["rate"] == 3.5
        assert snippet_restored.source_packet_id == packet.packet_id
        assert snippet_restored.quality_score == 0.85

    def test_timestamp_preservation(self) -> None:
        """Test: Timestamps werden korrekt über Serialisierung erhalten."""
        now = datetime.now(timezone.utc)

        event = IntelEvent(source="TEST", created_at=now)
        packet = InfoPacket(intel_event=event, created_at=now)
        snippet = LearningSnippet(created_at=now)

        # Roundtrip
        event_restored = IntelEvent.from_dict(event.to_dict())
        packet_restored = InfoPacket.from_dict(packet.to_dict())
        snippet_restored = LearningSnippet.from_dict(snippet.to_dict())

        # Timestamps sollten gleich sein (auf Sekunden-Ebene)
        assert event_restored.created_at.replace(microsecond=0) == now.replace(
            microsecond=0
        )
        assert packet_restored.created_at.replace(microsecond=0) == now.replace(
            microsecond=0
        )
        assert snippet_restored.created_at.replace(microsecond=0) == now.replace(
            microsecond=0
        )
