# E19 Architecture

The Command Center is a read-oriented aggregation surface. Domain tables remain authoritative. It does not copy workflow state or bypass domain permissions. Queue counts are computed inside the tenant session and attention items are derived from explicit operational states.
