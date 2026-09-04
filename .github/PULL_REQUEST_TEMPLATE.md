## Summary
<!-- What does this PR do? -->

## Type of change
- [ ] Bug fix
- [ ] New feature / agent capability
- [ ] Infrastructure / deployment change
- [ ] Security fix
- [ ] Documentation

## Testing
- [ ] Tests written first (TDD RED → GREEN)
- [ ] All existing tests still passing (`pytest tests/ -q`)
- [ ] New tests cover the change

## HIPAA / Security checklist
- [ ] No PHI hardcoded in any file
- [ ] No secrets or API keys committed
- [ ] HIPAA audit log fires for any new PHI-touching operation
- [ ] New endpoints have rate limiting if public-facing
- [ ] AI Shield bridge called for new agent prompts

## Ecosystem
- [ ] FusionOps bridge notified of any new event types
- [ ] No direct product-to-product connections added
- [ ] `.env.example` updated if new env vars added

## Related issues
Closes #
