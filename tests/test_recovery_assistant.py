import pytest
from modules.recovery_assistant import RecoveryAssistant, RECOVERY_CASES


def test_recovery_cases_keys():
    assistant = RecoveryAssistant()
    for case_id in ["A", "B", "C", "D", "E"]:
        case_data = assistant.get_case(case_id)
        assert case_data is not None
        assert "title" in case_data
        assert "summary" in case_data
        assert len(case_data["steps"]) > 0


def test_invalid_case():
    assistant = RecoveryAssistant()
    assert assistant.get_case("Z") is None
