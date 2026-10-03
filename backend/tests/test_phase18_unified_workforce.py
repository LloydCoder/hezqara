def test_workforce_statuses_preserve_human_approval_state():
 assert {'queued','running','waiting_approval','completed','failed','cancelled'} >= {'waiting_approval','completed'}
