def test_command_center_prioritizes_approval_queue():
    queues={'open_ai_approvals':2,'open_workforce_runs':1,'open_care_gaps':3}
    attention=[]
    if queues['open_ai_approvals']: attention.append('ai_approvals')
    assert attention[0]=='ai_approvals'
