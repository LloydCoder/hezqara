from typing import Final

CLAIM_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
 'draft': frozenset({'ready'}), 'ready': frozenset({'submitted'}),
 'submitted': frozenset({'accepted','rejected','pending'}),
 'accepted': frozenset({'paid','partially_paid','denied'}),
 'rejected': frozenset({'ready','closed'}), 'pending': frozenset({'accepted','rejected','denied','closed'}),
 'paid': frozenset({'closed'}), 'partially_paid': frozenset({'closed','denied'}),
 'denied': frozenset({'appealed','closed'}), 'appealed': frozenset({'accepted','rejected','paid','closed'}), 'closed': frozenset()
}
PAYMENT_STATES = frozenset({'pending','authorized','paid','failed','refunded','voided'})

def validate_claim_transition(current: str, target: str) -> None:
    if target not in CLAIM_TRANSITIONS.get(current, frozenset()):
        raise ValueError(f'invalid claim transition: {current} -> {target}')

def validate_payment_state(state: str) -> None:
    if state not in PAYMENT_STATES: raise ValueError(f'invalid payment state: {state}')

def aging_bucket(days: int) -> str:
    if days < 0: raise ValueError('days cannot be negative')
    if days <= 30: return '0_30'
    if days <= 60: return '31_60'
    if days <= 90: return '61_90'
    if days <= 120: return '91_120'
    return '120_plus'
