# External Benchmark Directions

This document maps each major archetype to a small set of external product references that set a strong visual and product-quality bar.

Use these references for:
- deciding what "good" should look like before promoting local builds into `eval/archetype_benchmarks.json`
- extracting transferable layout, hierarchy, interaction, and polish traits
- avoiding benchmark drift toward local-but-mediocre outputs

Do not copy third-party code. Use these products as design and product-shape references, then capture the same quality bar with committed portable local benchmark builds.

## How To Use

When evaluating a local candidate benchmark:
- prefer product references that match the archetype's real interaction model, not just its color palette
- favor transferable system qualities over one-off visual gimmicks
- promote local examples that clearly express 3-5 of the target traits below
- reject examples that only mimic a surface look without matching the underlying product behavior

## Dashboard

Primary references:
- [Linear](https://linear.app/)
- [Stripe Payments](https://stripe.com/payments)

Target traits:
- strong information hierarchy with immediate top-level orientation
- dense but calm layout with disciplined spacing
- premium panel framing without noisy decoration
- clear state emphasis for the most important numbers and actions
- system-level polish over flashy dashboard chrome

What to avoid:
- oversized empty cards
- decorative charts with weak data framing
- generic "dark admin template" styling

## Fintech

Primary references:
- [Stripe Payments](https://stripe.com/payments)
- [Stripe Checkout](https://stripe.com/checkout)
- [Linear](https://linear.app/)

Target traits:
- trust-building precision and clarity
- typography that makes figures and status states easy to scan
- high-confidence layout discipline
- controlled accent use around money, performance, and state
- premium utility feel rather than startup-dashboard clutter

What to avoid:
- playful or soft UI language that undercuts credibility
- weak numeric contrast or non-deliberate tabular rhythm
- shallow cards with no sense of product rigor

## Editor

Primary references:
- [Notion Docs](https://www.notion.com/product/docs)
- [Notion Wikis](https://www.notion.com/product/wikis)
- [Linear](https://linear.app/)

Target traits:
- obvious workspace framing with a clear primary canvas
- sidebar, outline, comments, and inspector surfaces that feel productized
- collaboration cues that are visible without cluttering the page
- restrained premium typography and spacing
- tool affordances that feel real, not decorative

What to avoid:
- using generic dashboard or calculator layouts as editor references
- over-indexing on one central card without workspace context
- fake toolbars with no clear editing hierarchy

## Form

Primary references:
- [Typeform](https://www.typeform.com/)
- [Typeform Forms](https://www.typeform.com/forms/)

Target traits:
- guided progression that feels lightweight and confidence-building
- clear step framing, pacing, and completion momentum
- polished success, validation, and error states
- low-friction input surfaces with strong completion cues
- productized onboarding feel, not just a stacked form

What to avoid:
- static settings panels mislabeled as multi-step flows
- overly dense screens with weak progression cues
- form UIs that never show convincing completion states

## SaaS Landing

Primary references:
- [Vercel](https://vercel.com/)
- [Framer](https://www.framer.com/)
- [Raycast](https://www.raycast.com/)

Target traits:
- strong hero hierarchy with immediate product positioning
- premium typography and restrained color discipline
- product storytelling through real interface framing, not abstract filler
- polished section rhythm across features, proof, pricing, FAQ, and CTA
- motion-aware composition even in static screenshots

What to avoid:
- generic purple-on-dark SaaS templates
- empty mockup frames and placeholder features
- repetitive card grids without a focal section

## Ecommerce

Primary references:
- [Shopify](https://www.shopify.com/)
- [Stripe Terminal](https://stripe.com/us/terminal)

Target traits:
- clear merchandising hierarchy
- premium product presentation with strong conversion rhythm
- polished checkout or cart-adjacent trust cues
- editorial structure where appropriate, but still commerce-first
- realistic product density and complete purchase flow framing

What to avoid:
- fashion-editorial mood without actual shopping clarity
- weak CTA hierarchy
- incomplete storefronts that stop at hero plus grid

## Portfolio

Primary references:
- [Framer](https://www.framer.com/)
- [Raycast](https://www.raycast.com/)

Target traits:
- strong personal brand point of view
- memorable hero hierarchy without sacrificing readability
- coherent project-card rhythm and case-study framing
- polished contact/CTA finish
- visual personality that still feels shippable and credible

What to avoid:
- broken media or empty project cards
- dashboard-like layouts accidentally scoring as portfolio
- flashy accents without a strong content hierarchy

## Game / Fan Experience

Primary references:
- [Framer](https://www.framer.com/)
- [Raycast](https://www.raycast.com/)

Use these as polish references, not literal content references.

Target traits:
- strong atmosphere and theme commitment
- premium card systems and modal reveals
- visible interaction density
- clear content sequencing across lore, characters, stats, and media
- collector-edition feel instead of generic fandom layout

What to avoid:
- flat landing-page structure with themed copy pasted on top
- weak media framing
- missing progression between hero, cast, and deeper content sections

## Promotion Rules

Promote a local build into `eval/archetype_benchmarks.json` when:
- it matches the archetype's true product shape
- it is visually competitive with the external direction above
- its strengths are transferable across prompts in the same archetype
- the notes can describe specific reusable traits

Use higher priority when:
- the build is archetype-defining
- the interaction model is especially transferable
- the design quality is consistently above the neighboring references

Use lower priority when:
- the example is useful but partial
- the build has a good structure but weaker finish
- the traits are narrow or less broadly reusable

Set `global_guidance: true` only when:
- the value is cross-archetype interaction or polish
- the example is not a literal benchmark for one archetype's layout
- the notes are still specific enough to be actionable

## Current Take

Based on the current local benchmark set:
- `editor`, `dashboard`, `fintech`, and `saas_landing` now have a clear enough external direction
- `portfolio` and `form` are improved but still benefit from one more strong benchmark each over time
- `ecommerce` should continue leaning into premium merchandising clarity rather than purely editorial mood
- `game` should keep using local themed benchmarks, with external references used only for polish and interaction standards

## Sources

Official pages referenced above:
- [Notion Docs](https://www.notion.com/product/docs)
- [Notion Wikis](https://www.notion.com/product/wikis)
- [Notion for Product](https://www.notion.com/product/notion-for-product)
- [Linear](https://linear.app/)
- [Typeform](https://www.typeform.com/)
- [Typeform Forms](https://www.typeform.com/forms/)
- [Vercel](https://vercel.com/)
- [Framer](https://www.framer.com/)
- [Raycast](https://www.raycast.com/)
- [Shopify](https://www.shopify.com/)
- [Stripe Payments](https://stripe.com/payments)
- [Stripe Checkout](https://stripe.com/checkout)
- [Stripe Terminal](https://stripe.com/us/terminal)
