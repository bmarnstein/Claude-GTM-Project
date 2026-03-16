# Revenue Experiments & Agents Plan for Oscilar

## Context

Based on the Ben/Jessica call recap, Oscilar's GTM has three key gaps: (1) event workflows are manual and overwhelming Jessica, (2) AE enablement is the biggest pipeline blocker, and (3) outbound needs to be more event-integrated rather than purely automated. The existing Account Intel Bot (`/intel`) already provides strong research, pain point, and outreach infrastructure via Slack + Claude + Notion + Tavily. These experiments and agents extend that foundation.

---

## Experiments

### Experiment 1: Pre-Event Intel Blitz
**Hypothesis:** Running `/intel` on all ~100 priority contacts before an event (e.g., FinTech Meetup) and surfacing personalized talking points will increase meaningful conversations by 2-3x vs. generic prep.

**What to build:**
- New `/event-prep <event-name>` Slack command that accepts a CSV of companies/contacts
- Batch-runs the existing intel pipeline for each company
- Generates a **1-page event briefing** per contact: company pain points, trigger events, and a personalized conversation opener
- Posts a summary digest to a Slack channel + creates a Notion event dashboard

**Success metric:** Number of qualified meetings booked at FinTech Meetup vs. previous events
**Effort:** Medium (1-2 weeks) — reuses existing analysis modules, adds batch orchestration + event briefing prompt

**Files to modify:** `app.py` (new command handler), new `analysis/event_briefing.py`, new `prompts/system_event_briefing.py`, `integrations/notion_client.py` (event dashboard)

---

### Experiment 2: Event Invite Sequencing Agent
**Hypothesis:** A structured 3-touch invite sequence (email invite → Paperless Post → LinkedIn/HeyReach follow-up) with personalized messaging per contact tier will increase event attendance by 30-50%.

**What to build:**
- New `/event-invite <event-name>` command that takes the enriched contact list
- Uses existing persona analysis to customize invite language per buyer type
- Generates 3 assets per contact: email copy, Paperless Post message, LinkedIn note
- Outputs a ready-to-execute campaign sheet (CSV) for HeyReach import + Paperless Post
- Tracks RSVPs in Notion with status updates

**Success metric:** RSVP rate and attendance rate vs. baseline (manual invites)
**Effort:** Medium (1-2 weeks) — extends outreach.py with event-specific templates

**Files to modify:** new `analysis/event_invites.py`, new `prompts/system_event_invite.py`, `integrations/notion_client.py`

---

### Experiment 3: AE Event Enablement Kit
**Hypothesis:** Providing AEs with auto-generated, event-specific enablement materials (attendee briefs, talk tracks, follow-up templates) 48 hours before an event will improve post-event conversion rates.

**What to build:**
- Triggered automatically when event-prep runs (Experiment 1)
- Generates per-AE packets: their assigned accounts' briefs, suggested conversation starters, competitive positioning for likely objections, and follow-up email templates
- Posts to a dedicated `#ae-enablement` Slack channel and DMs each AE their packet
- Includes a "Day After" follow-up prompt that auto-generates personalized follow-ups based on meeting notes

**Success metric:** AE follow-up rate within 48 hours post-event; pipeline created from event contacts within 30 days
**Effort:** Medium (2 weeks) — combines intel outputs with new enablement prompt layer

**Files to modify:** new `analysis/ae_enablement.py`, new `prompts/system_ae_enablement.py`, `integrations/slack_messages.py`

---

### Experiment 4: Integrated Campaign Narrative Engine
**Hypothesis:** Campaigns tied to a cohesive narrative theme (e.g., "The End of Rules-Based Fraud Detection") will generate 2x more engagement than standalone product-pitch outreach.

**What to build:**
- New `/campaign-theme <theme>` command that generates a full campaign kit:
  - Theme narrative (blog post outline, event talk abstract, webinar pitch)
  - 3 persona-specific outreach sequences aligned to the theme
  - Social proof mapping (which Oscilar case studies/stats support this theme)
  - Event tie-in suggestions (which upcoming events align)
- Builds on Alan's existing campaign structure work

**Success metric:** Reply rate on themed outreach vs. generic outreach
**Effort:** Medium (1-2 weeks) — new prompt + orchestration, reuses persona/outreach modules

**Files to modify:** new `analysis/campaign_theme.py`, new `prompts/system_campaign_theme.py`, `app.py`

---

### Experiment 5: Post-Event Pipeline Accelerator
**Hypothesis:** Automated, personalized follow-ups within 24 hours of an event — referencing specific conversation topics — will convert 3x more event contacts to pipeline vs. generic follow-ups.

**What to build:**
- New `/event-followup <event-name>` command
- AEs/BDRs log brief meeting notes in Slack (or a simple form)
- Agent combines meeting notes + pre-event intel to generate hyper-personalized follow-up emails
- Auto-assigns follow-up ownership (BDR vs. AE) based on account tier rules
- Tracks follow-up completion in Notion

**Success metric:** Meeting-to-opportunity conversion rate from events
**Effort:** Low-Medium (1 week) — mostly prompt engineering on top of existing data

**Files to modify:** new `analysis/event_followup.py`, new `prompts/system_event_followup.py`, `app.py`

---

### Experiment 6: Sales-Facing Event Calendar Bot
**Hypothesis:** A single source of truth for events (with auto-populated attendee intel and AE assignments) will reduce event prep chaos and increase AE participation.

**What to build:**
- Notion-based event calendar with structured fields: event name, date, type, target accounts, AE assignments, status, materials links
- `/events` Slack command to list upcoming events with prep status
- Auto-reminders at T-2 weeks ("intel blitz needed"), T-2 days ("enablement kits ready"), T+1 day ("follow-ups due")
- Integrates with Experiments 1, 3, and 5 as the orchestration layer

**Success metric:** Reduction in Jessica's manual coordination time; AE satisfaction score
**Effort:** Medium (1-2 weeks) — Notion schema + Slack command + reminder logic

**Files to modify:** new `integrations/event_calendar.py`, `app.py`, `integrations/notion_client.py`

---

## Agents to Build

### Agent 1: Event Command Center Agent
**Trigger:** `/event <event-name> <action>` (prep | invite | followup | status)
**What it does:** Unified orchestrator for the entire event lifecycle — wraps Experiments 1, 2, 3, 5, and 6 into a single agent that manages event workflow end-to-end.
**Integrations:** Slack, Notion, Claude, Tavily, CSV import/export (for HeyReach)
**Extends:** `app.py` as a new top-level command handler that delegates to sub-modules

### Agent 2: AE Enablement Agent
**Trigger:** `/enable <account-name>` or auto-triggered before events
**What it does:** Generates on-demand account briefs, competitive battlecards, talk tracks, and follow-up templates for a specific account. Combines existing `/intel` data with Oscilar-specific competitive positioning and relevant case studies.
**Integrations:** Slack, Notion (reads existing account pages), Claude
**Extends:** Existing `analysis/` pipeline with new enablement-focused prompts; reads from Notion rather than re-running research when data is fresh

### Agent 3: Contact List Enrichment Agent
**Trigger:** `/enrich <csv-upload>` or triggered as part of event-prep
**What it does:** Takes a raw event contact list and enriches it with: company intel (from existing pipeline), persona classification, account tier, pain point relevance score, and suggested outreach angle. Outputs an enriched CSV ready for HeyReach/Paperless Post campaigns.
**Integrations:** Slack (file upload), Tavily, Claude, CSV processing
**Extends:** `research/aggregator.py` + `analysis/persona_analysis.py` in batch mode

### Agent 4: Campaign Narrative Agent
**Trigger:** `/campaign <theme-keyword>`
**What it does:** Generates integrated campaign materials around a theme — outreach sequences, event talk abstracts, blog outlines, and social proof mapping. Ensures all outbound, events, and content tell a cohesive story.
**Integrations:** Slack, Claude, Notion (campaign tracking)
**Extends:** `analysis/outreach.py` with theme-aware prompt layer

---

## Priority Order (based on call urgency)

| Priority | Item | Rationale |
|----------|------|-----------|
| **P0** | Experiment 1: Pre-Event Intel Blitz | FinTech Meetup is imminent; highest immediate ROI |
| **P0** | Agent 3: Contact List Enrichment | Jessica needs list enrichment NOW for FinTech Meetup + Fraud Fight Club |
| **P1** | Experiment 2: Event Invite Sequencing | Directly addresses the Paperless Post + HeyReach workflow |
| **P1** | Experiment 5: Post-Event Follow-up | Addresses the #1 blocker (AE follow-up) |
| **P1** | Agent 2: AE Enablement Agent | Tackles the biggest pipeline blocker identified in the call |
| **P2** | Experiment 3: AE Event Enablement Kit | Builds on P0/P1 work |
| **P2** | Experiment 6: Event Calendar Bot | Reduces Jessica's coordination burden |
| **P2** | Agent 1: Event Command Center | Unifies all event workflows |
| **P3** | Experiment 4: Campaign Narrative Engine | Important but less urgent; Alan already started |
| **P3** | Agent 4: Campaign Narrative Agent | Builds on Alan's work when ready |

---

## Verification / How to Test

1. **Unit test each new Slack command** with mock data before connecting live APIs
2. **Pilot Experiment 1 + Agent 3** on the FinTech Meetup contact list (~100 contacts) as first live test
3. **Measure:** RSVP rates, meeting quality scores, follow-up completion rates, and pipeline attribution per event
4. **Compare:** Event-sourced pipeline metrics vs. pure outbound pipeline metrics to validate Ben's hypothesis that events > automated outbound for enterprise

---

## Key Files in Existing Codebase to Reuse

- `account-intel-bot/app.py` — Command handler pattern, extend for new `/event-*` commands
- `account-intel-bot/research/aggregator.py` — Batch research orchestration (parallelize for lists)
- `account-intel-bot/analysis/pain_points.py` — Pain point scoring (reuse for contact prioritization)
- `account-intel-bot/analysis/persona_analysis.py` — Persona classification (reuse for contact enrichment)
- `account-intel-bot/analysis/outreach.py` — Outreach generation (extend for event-specific templates)
- `account-intel-bot/integrations/notion_client.py` — Notion CRUD (extend for event dashboards)
- `account-intel-bot/integrations/slack_messages.py` — Threaded messaging (reuse for all new agents)
- `account-intel-bot/prompts/oscilar_context.py` — Product/competitive context (reuse across all new prompts)
