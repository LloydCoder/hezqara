import pytest
from app.domains.workflows.service import LEGAL_RUN_TRANSITIONS


def test_workflow_run_state_machine_has_no_terminal_transitions():
    assert LEGAL_RUN_TRANSITIONS['completed'] == set()
    assert LEGAL_RUN_TRANSITIONS['cancelled'] == set()


def test_workflow_run_state_machine_requires_running_before_completion():
    assert 'completed' in LEGAL_RUN_TRANSITIONS['running']
    assert 'completed' not in LEGAL_RUN_TRANSITIONS['queued']


def test_workflow_run_state_machine_supports_approval_gate():
    assert 'waiting_for_approval' in LEGAL_RUN_TRANSITIONS['running']
    assert 'running' in LEGAL_RUN_TRANSITIONS['waiting_for_approval']

@pytest.mark.parametrize('status,target', [('completed','running'),('cancelled','queued'),('queued','completed')])
def test_invalid_state_transitions_are_not_legal(status,target):
    assert target not in LEGAL_RUN_TRANSITIONS[status]
