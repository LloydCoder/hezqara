# E20 Architecture

Agent → governance → tool policy → MCP/native/FHIR/REST adapter → external system → evidence/audit.

The policy layer precedes tool execution. MCP can expose capabilities but cannot grant authority. The same governed capability may use MCP or another transport without changing its risk policy.
