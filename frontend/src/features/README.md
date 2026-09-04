# Frontend feature boundaries

Domain UI belongs under `features/<domain>`. App Router pages should remain thin route adapters that compose feature components. Shared components must remain presentation-only and must not contain authorization logic or direct database access.
