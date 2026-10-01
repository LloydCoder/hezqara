# Access Review & Privilege Management

## Review model

Access reviews are tenant scoped and record:

- subject identity;
- current role;
- permission snapshot;
- reviewer;
- decision;
- review timestamp;
- next review date;
- supporting evidence.

## Rules

- Access is granted by server-side authorization, not by UI state.
- Organization role and permission changes must be audited.
- Privileged roles receive periodic review.
- Dormant or departed users must be revoked through the identity provider.
- Integration credentials use least privilege and separate production/test identities.
- Service-role/system contexts are not exposed through request handlers.

The review record is evidence; it does not itself grant or revoke access.
