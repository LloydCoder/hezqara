# HEZQARA brand identity

**Authority:** HEZQARA Logo & Brand Usage Guidelines, Brand Identity Kit v1.0, November 2026.

This document records the canonical implementation rules for the HEZQARA web application. The supplied brand kit and its 13-page guidelines remain the source of truth.

## Approved identity

- Primary lockup: horizontal logo with tagline.
- Compact lockup: horizontal logo without tagline.
- Standalone mark: avatars, favicons and constrained application surfaces.
- Wordmark and tagline are supplied as outlined vector artwork. Never recreate them as live text or CSS.
- Use supplied artwork without stretching, rotation, recolouring, effects or rearrangement.

## Web asset mapping

| Asset | Use |
| --- | --- |
| `/brand/hezqara-logo-horizontal-tagline-full-color.svg` | Primary lockup on light surfaces |
| `/brand/hezqara-logo-horizontal-full-color.svg` | Compact lockup on light surfaces |
| `/brand/hezqara-logo-horizontal-reversed.svg` | Compact lockup on dark surfaces |
| `/brand/hezqara-logo-mark-full-color.svg` | Standalone mark on light surfaces |
| `/brand/hezqara-mark-small-size-full-color.svg` | Heavier mark below 32 px on light surfaces |
| `/brand/hezqara-mark-small-size-reversed.svg` | Heavier mark below 32 px on dark surfaces |
| `/brand/hezqara-logo-mark-reversed.svg` | Standalone mark on dark surfaces |
| `/favicon.ico` | Broad browser favicon fallback |
| `/favicon.svg` | Primary vector browser favicon |
| `/apple-touch-icon.png` | iOS home-screen icon |
| `/safari-pinned-tab.svg` | Safari pinned tab |
| `/site.webmanifest` | Application name and icon metadata |

The supplied vector artwork is retained. The embedded C2PA metadata is omitted from the web-delivery copies; the visual paths, geometry and colours are preserved.

## Colour tokens

| Token | Value | Use |
| --- | --- | --- |
| Navy | `#0F2A47` | Primary identity |
| Teal | `#14B8A6` | Logo and graphic accent |
| Teal Deep | `#0F766E` | Text, links and buttons on light backgrounds |
| Teal Bright | `#2DD4BF` | Accent on dark backgrounds |
| Midnight | `#0B1220` | Dark surfaces |
| Slate | `#5B6B7F` | Secondary text |
| Mist | `#9AA8BA` | Secondary text on dark |
| Ice | `#F4F8FB` | Light surfaces |
| White | `#FFFFFF` | Backgrounds |

Teal `#14B8A6` must not be used for small text on white; its contrast is insufficient. Use Teal Deep for text and links.

## Typography

Use Inter Regular and Bold. Keep Medium and SemiBold sparing in product UI. Use the outlined supplied wordmark and tagline rather than retyping either.

## Approved brand language

- Tagline: **The governed AI workforce for healthcare**
- Descriptor: **A governed AI workforce for healthcare front-office operations.**
- Voice: calm, precise and accountable.
- Write the name as **HEZQARA** in headings and running text.
- Retire Carenova from new materials. A transition note may say “HEZQARA (formerly Carenova AI)” for a limited period only.

Do not make HIPAA, GDPR, ISO 27001 or other compliance claims unless the certification and evidence exist.

## Implementation requirements

- Keep the primary logo at or above its 260 px digital minimum width.
- Below 120 px wide, use the compact horizontal lockup without tagline.
- Below 32 px tall, use the supplied heavier small-size mark.
- Maintain clear space equal to half the mark height.
- Use supplied SVG artwork for web logos and vector favicons; use the supplied PNG for the Apple touch icon.
- Keep the web manifest and browser icon links pointed at real, tested static assets.
- Use the HEZQARA Open Graph image endpoint for social previews; do not bake the temporary Vercel hostname into the artwork.
- Keep light and dark logo variants matched to their actual backgrounds.
- Update the Open Graph image and canonical domain when the final production domain is selected.

## Source

See `Hezqara-Brand-Guidelines.pdf` in the official brand kit. This implementation note does not replace the supplied PDF.
