# Prompt Library

Use these as patterns, not rigid scripts.

## Hidden Session Strategy Prompt

```text
You are starting a reading session.
Proceed only after the co-reading frontend is open; otherwise launch it and wait for confirmation.
Load the user's active reading profile, current book state, recent sessions, and open cards.
Use the profile as default context, but obey the user's current request first.
Do not ask whether to save profile data.
During the session, silently capture progress, card evidence, and profile signals.
```

## First Response After Book Resolution

```text
I found <book/source> and prepared the local reading workspace.
Open the co-reading reader here: http://127.0.0.1:8768/共读.html
You should see <book/source>, the reading area, and the co-reading panel.
Tell me when the page is open; then we will continue from <position>.
```

## Vague Reading Request With No Active Book

```text
We can start. Which book do you want to read, and where should I search for the file?
If you do not have a local file yet, we can start in excerpt-driven mode and you can paste passages as you read.
```

## Vague Reading Request With Active Book

```text
You have <active book> open at <saved position>.
Do you want to continue from there, or start a new book?
```

## Multiple Source Matches

```text
I found several possible sources for <book title>:
1. <file name> · <type> · <path>
2. <file name> · <type> · <path>
Which one should I use for this reading workspace?
```

## Source Confirmation Before Initialization

```text
I will initialize the reading workspace with:
- Book: <title>
- Source: <path or user-input-driven>
- Frontend: co-reading reader + dashboard

After this, the user opens the reader; no manual HTML editing is needed.
```

## Frontend Launch Failure

```text
The reader is not ready yet: <specific symptom>.
I am going to fix <launcher/config/dependency/port issue> first.
We should not continue the reading in chat until the co-reading page opens, because the page is where highlights, source position, and conversation state stay aligned.
```

## Excerpt Response Pattern

```text
This passage is doing <book claim>.
The part that may matter is <specific tension or idea>.
If we turn it into a card, the current draft is <card seed>.
The missing piece is your angle: <one concrete, content-derived question>.
```

## No-Profile Reading Plan Prompt

```text
The user has no active reading plan for <book>.
Do not assume their identity, job, goals, or use case.
Offer two paths:
1. Ask three lightweight questions: why read, how deep to read, what to produce.
2. Generate a generic plan from the book/source and update it later from highlights and conversation.
```

## Highlight Button Intent Prompt

```text
The user clicked <tag> on this excerpt:
<quote>

Respond to the tag as an interaction intent, not as a final card request.
Include the source context, explain what this tag usually means, and ask for the missing user contribution when card formation needs it.
For "反对", first steelman the author, then identify assumptions, possible counterexamples, and ask whether the user's disagreement is about facts, values, or applicability.
```

## Packaging Review Prompt

```text
Review this reading-companion skill package for reuse.
Check only reusable skill files and references, not generated user workspaces.
Flag private paths, creator-specific names, real reading history, bundled private books, enabled private harness settings, missing launch instructions, stale static-server instructions, and missing validation steps.
Return a concise fix list with file paths.
```

## Profile Signal Extraction Prompt

```text
Review this session transcript.
Extract only evidence-backed reading preferences or corrections.
Do not infer identity or life context.
Return JSONL signals with level, evidence, confidence, and action.
Prefer low confidence unless the user explicitly states a preference.
```

## Profile Consolidation Prompt

```text
Given active profile entries and new profile signals:
1. Keep current corrections above old preferences.
2. Merge repeated L2 preferences.
3. Leave L3 observations as candidates unless explicitly confirmed.
4. Add exceptions rather than duplicating conflicting preferences.
5. Preserve evidence and last_activated.
```

## Card Finalization Prompt

```text
Given the source excerpt, conversation, and draft card:
Decide whether the card is draft, in_progress, or final.
It can be final only if the user supplied a trigger, interpretation, example, disagreement, or application.
Return the card in the required schema.
```
