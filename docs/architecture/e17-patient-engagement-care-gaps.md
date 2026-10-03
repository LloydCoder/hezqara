# E17 Architecture — Patient Engagement & Care Gaps

E17 consumes authorized care-gap/recall signals and turns them into reviewable patient-engagement proposals. It does not independently infer a diagnosis or clinical need.

Flow:

authorized care-gap evidence → outreach proposal → preference/consent checks → human approval → existing communication queue/provider boundary → delivery events.

The initial implementation owns the care-gap and proposal state; the existing communication subsystem remains the outbound provider boundary. This prevents E17 from duplicating messaging infrastructure.
