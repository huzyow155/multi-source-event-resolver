import json
import pytest


def test_initial_state(direct_deploy):
    contract = direct_deploy("contracts/contract.py")
    assert contract.get_event_count() == 0
    assert contract.has_event("evt-nonexistent") is False

    with pytest.raises(Exception) as excinfo:
        contract.get_latest_event()
    assert "No events resolved yet" in str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        contract.get_event_id_at(0)
    assert "Index out of bounds" in str(excinfo.value)


def test_resolve_event_happened(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/contract.py")

    direct_vm.mock_web(
        "https://source1.org/news",
        {"method": "GET", "status": 200, "body": "SpaceX caught the booster on the launch tower successfully."}
    )
    direct_vm.mock_web(
        "https://source2.com/report",
        {"method": "GET", "status": 200, "body": "Starship flight 5 booster was successfully captured."}
    )

    llm_payload = {
        "verdict": "HAPPENED",
        "confidence": "HIGH",
        "source1_status": "CONFIRMS",
        "source2_status": "CONFIRMS",
        "summary": "Both independent sources confirm the booster catch occurred."
    }
    direct_vm.mock_llm(".*", json.dumps(llm_payload))

    contract.resolve_event(
        "evt-flight-5",
        "SpaceX Starship flight 5 booster catch",
        "https://source1.org/news",
        "https://source2.com/report"
    )

    assert contract.get_event_count() == 1
    assert contract.has_event("evt-flight-5") is True

    ev = contract.get_event("evt-flight-5")
    assert ev.id == "evt-flight-5"
    assert ev.verdict == "HAPPENED"
    assert ev.confidence == "HIGH"
    assert ev.source1_status == "CONFIRMS"
    assert ev.source2_status == "CONFIRMS"
    assert "Both independent sources" in ev.summary

    latest = contract.get_latest_event()
    assert latest.id == "evt-flight-5"
    assert contract.get_event_id_at(0) == "evt-flight-5"


def test_resolve_event_not_happened(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/contract.py")

    direct_vm.mock_web(
        "https://news.org/spacex",
        {"method": "GET", "status": 200, "body": "The planned orbital test was scrubbed."}
    )
    direct_vm.mock_web(
        "https://aerospace.com/update",
        {"method": "GET", "status": 200, "body": "Launch postponed due to weather."}
    )

    llm_payload = {
        "verdict": "NOT_HAPPENED",
        "confidence": "HIGH",
        "source1_status": "REFUTES",
        "source2_status": "REFUTES",
        "summary": "Both sources confirm the test was scrubbed and postponed."
    }
    direct_vm.mock_llm(".*", json.dumps(llm_payload))

    contract.resolve_event(
        "evt-flight-postponed",
        "Flight launched on scheduled date",
        "https://news.org/spacex",
        "https://aerospace.com/update"
    )

    ev = contract.get_event("evt-flight-postponed")
    assert ev.verdict == "NOT_HAPPENED"
    assert ev.confidence == "HIGH"


def test_resolve_event_conflicting_evidence(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/contract.py")

    direct_vm.mock_web(
        "https://sourceA.com/story",
        {"method": "GET", "status": 200, "body": "CEO announced resignation effective immediately."}
    )
    direct_vm.mock_web(
        "https://sourceB.com/story",
        {"method": "GET", "status": 200, "body": "Spokesperson denies CEO resignation rumors."}
    )

    llm_payload = {
        "verdict": "CONFLICTING_EVIDENCE",
        "confidence": "MEDIUM",
        "source1_status": "CONFIRMS",
        "source2_status": "REFUTES",
        "summary": "Source 1 claims resignation occurred while Source 2 reports official denial."
    }
    direct_vm.mock_llm(".*", json.dumps(llm_payload))

    contract.resolve_event(
        "evt-ceo-resignation",
        "CEO has officially resigned from the company",
        "https://sourceA.com/story",
        "https://sourceB.com/story"
    )

    ev = contract.get_event("evt-ceo-resignation")
    assert ev.verdict == "CONFLICTING_EVIDENCE"
    assert ev.confidence == "MEDIUM"
    assert ev.source1_status == "CONFIRMS"
    assert ev.source2_status == "REFUTES"


def test_resolve_event_unresolved_evidence(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/contract.py")

    direct_vm.mock_web(
        "https://neutral1.org/page",
        {"method": "GET", "status": 200, "body": "General market commentary with no mention of merger."}
    )
    direct_vm.mock_web(
        "https://neutral2.org/page",
        {"method": "GET", "status": 200, "body": "Industry trends review."}
    )

    llm_payload = {
        "verdict": "UNRESOLVED",
        "confidence": "LOW",
        "source1_status": "NEUTRAL",
        "source2_status": "NEUTRAL",
        "summary": "Neither source contains information regarding the proposed merger."
    }
    direct_vm.mock_llm(".*", json.dumps(llm_payload))

    contract.resolve_event(
        "evt-merger-rumor",
        "Company A merged with Company B",
        "https://neutral1.org/page",
        "https://neutral2.org/page"
    )

    ev = contract.get_event("evt-merger-rumor")
    assert ev.verdict == "UNRESOLVED"
    assert ev.confidence == "LOW"


def test_double_resolution_rejection(direct_vm, direct_deploy):
    contract = direct_deploy("contracts/contract.py")

    direct_vm.mock_web(".*", {"method": "GET", "status": 200, "body": "Sample news content"})
    llm_payload = {
        "verdict": "HAPPENED",
        "confidence": "HIGH",
        "source1_status": "CONFIRMS",
        "source2_status": "CONFIRMS",
        "summary": "Confirmed"
    }
    direct_vm.mock_llm(".*", json.dumps(llm_payload))

    contract.resolve_event(
        "evt-duplicate-check",
        "Test event description",
        "https://s1.org/news",
        "https://s2.org/news"
    )

    # Attempting to resolve again with identical ID must raise UserError
    with pytest.raises(Exception) as excinfo:
        contract.resolve_event(
            "evt-duplicate-check",
            "Different description",
            "https://s1.org/news",
            "https://s2.org/news"
        )
    assert "already been resolved" in str(excinfo.value)


def test_validation_errors(direct_deploy):
    contract = direct_deploy("contracts/contract.py")

    # Empty event_id
    with pytest.raises(Exception) as excinfo:
        contract.resolve_event("", "Valid description here", "https://s1.org", "https://s2.org")
    assert "event_id cannot be empty" in str(excinfo.value)

    # Description too short
    with pytest.raises(Exception) as excinfo:
        contract.resolve_event("id-1", "bad", "https://s1.org", "https://s2.org")
    assert "at least 5 characters" in str(excinfo.value)

    # Invalid URL scheme
    with pytest.raises(Exception) as excinfo:
        contract.resolve_event("id-2", "Valid description", "ftp://s1.org", "https://s2.org")
    assert "valid HTTP or HTTPS URL" in str(excinfo.value)

    with pytest.raises(Exception) as excinfo:
        contract.resolve_event("id-3", "Valid description", "https://s1.org", "not-a-url")
    assert "valid HTTP or HTTPS URL" in str(excinfo.value)

    # Non-independent sources (same URL)
    with pytest.raises(Exception) as excinfo:
        contract.resolve_event("id-4", "Valid description", "https://s1.org/item", "https://s1.org/item")
    assert "distinct independent sources" in str(excinfo.value)

    # Querying nonexistent event
    with pytest.raises(Exception) as excinfo:
        contract.get_event("nonexistent-id")
    assert "Event ID not found" in str(excinfo.value)
