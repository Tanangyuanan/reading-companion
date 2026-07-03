# Card Schema

Knowledge cards must be interaction-based.

## Status

- `draft`: AI-generated candidate from source text or excerpt.
- `in_progress`: user has reacted, questioned, disagreed, or supplied a context, but the card still needs shaping.
- `final`: user contribution is present and the card is usable outside this reading session.

Never mark a card final from AI summary alone.

## Card Types

- `concept`: explains a useful idea.
- `method`: guides action.
- `case`: preserves a reusable example.
- `question`: captures an unresolved but important question.
- `counterpoint`: captures disagreement, limits, or boundary conditions.

## Required Fields

```markdown
# <card title>

- id:
- status: draft | in_progress | final
- type:
- source:
- source_mode: source-backed | excerpt-backed | user-input-driven
- user_trigger:
- user's_words:
- book_claim:
- interpretation:
- boundary:
- reusable_for:
- next_action:
- linked_cards:
```

## Finalization Checklist

Before final:

- The source or excerpt is identified.
- The user's contribution is present.
- The card has a boundary or caveat.
- The card names where it can be reused.
- The card is not just a chapter summary.
