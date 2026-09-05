# HEZQARA design system

## Principles

HEZQARA is an operational healthcare product, not a generic AI chat interface. UI should favor trust, hierarchy, accountability, human oversight, auditability, and calm information density.

Production interfaces must never manufacture patient, task, execution, analytics, audit, notification, savings, or ROI data.

## Tokens

Global semantic CSS custom properties live in `frontend/src/app/globals.css`. Components should consume semantic utility classes or component-level variants rather than scattering raw colors.

The base system defines background, surface, foreground, muted text, borders, primary, status, and focus tokens. Typography uses the platform system sans stack so production builds do not depend on a remote font service.

## Component patterns

Reusable UI primitives live under `frontend/src/components/ui/`:

- primitives: Button, LinkButton, Card, Badge, StatusBadge, Metric, EmptyState, LoadingState, ErrorState, Skeleton
- forms: FormField, Input, Textarea, Select, SearchInput, FieldHint, FieldError
- data: DataTable, TableToolbar, DefinitionList, Timeline, ActivityList
- layout: ContentContainer, PageSection, Stack, Grid, PageHeader, Breadcrumbs
- AI: AgentBadge, AgentIdentity, AgentStatus, ConfidenceIndicator, EscalationBanner, ApprovalPanel, ExecutionSummary, ExecutionTimeline, ToolInvocationRow, HumanApprovalControl, AIActivityIndicator, ConfirmationDialog
- navigation: CommandPalette

Prefer composition over page-specific copies.

## AI state semantics

Readiness is separate from runtime execution.

Readiness: `ready`, `unavailable`, `disabled`, `not_configured`.

Runtime: `queued`, `running`, `waiting_for_approval`, `completed`, `failed`, `escalated`, `cancelled`.

A registry/configuration response may establish readiness. It must not be presented as a live execution state. Runtime status requires an execution record from the backend.

## Accessibility

Target WCAG 2.2 AA. Use semantic HTML before ARIA. Interactive controls have visible focus treatment and usable pointer targets. Dialogs manage focus and Escape behavior. Forms use visible labels and explicit errors. Status is conveyed with text and not color alone. Respect `prefers-reduced-motion`.

## Responsive rules

Design from 320px upward. Preserve action hierarchy at mobile widths, allow data tables to scroll horizontally when columns cannot safely collapse, and avoid desktop-only hover interactions.

## Security

Never place secrets, access tokens, tenant authority, or unnecessary PHI in client storage, URLs, logs, analytics, or telemetry. Client visibility is not authorization. Protected data must remain protected at the resource/API layer.

## Loading, error, and empty states

Use skeletons for known content structure, localized loading states for localized requests, actionable errors without stack traces, and explicit empty states when production data is absent. Never add synthetic records to make a surface appear complete.

## Contribution rules

New components should:

1. have typed props and semantic variants;
2. avoid domain logic in generic UI;
3. avoid new dependencies unless the bundle and accessibility trade-offs are justified;
4. avoid arbitrary raw colors and one-off status strings;
5. include keyboard and responsive behavior;
6. document any architectural exception.
