# Profile Schema

The reading profile is a visible, editable local file. It is not the skill itself.

## Files

- `profile.md`: active reading profile used at session start.
- `profile-signals.jsonl`: append-only evidence stream from sessions.
- `profile-candidates.md`: non-active candidate observations.
- `current-state.md`: current book and progress.

## Profile Levels

### L1 Runtime State

Examples: current book, chapter, last position, open cards.

Write automatically.

### L2 Reading Preferences

Examples: prefers questions over summaries, likes action cards, wants examples, dislikes generic summaries.

Record signals silently. Merge into `profile.md` only when evidence repeats or the preference is explicitly stated.

### L3 Identity and Long-Term Context

Examples: role, profession, long-term goals, personal situation, life constraints.

Do not silently activate. Keep as candidate unless the user explicitly asks to remember it.

## Profile Entry Format

```markdown
### <preference title>
- level: L2
- status: active
- confidence: low | medium | high
- strength: ★☆☆ | ★★☆ | ★★★
- source: session id or user quote
- evidence_count: 1
- last_activated: YYYY-MM-DD
- decay_rule: downgrade after 30 inactive days
- current_effect: how this changes future reading sessions
- exceptions:
  - current user intent overrides this preference
```

## Signal Format

Use one JSON object per line:

```json
{"timestamp":"YYYY-MM-DDTHH:mm:ssZ","book":"Book Title","session_id":"book-YYYYMMDD-HHMM","level":"L2","signal":"prefers action-oriented cards","evidence":"User chose action card over concept card","confidence":"low","action":"candidate"}
```

## Consolidation Rules

- Current user correction takes effect immediately in the current conversation.
- Repeated L2 signals can become active preferences.
- L3 signals stay candidates unless explicitly confirmed.
- Conflicting active preferences must be updated, downgraded, or marked with exceptions instead of duplicated.
- Every active preference needs evidence.
