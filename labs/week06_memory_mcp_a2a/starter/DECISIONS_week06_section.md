# Week 6: memory, a stateless MCP server, and an A2A channel

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 6

**Run conditions.** MCP SDK version: [2.3.0 ] | specification revision:
2026-07-28 | model: same | served locally | date: [2026-10-29]

### 1. The handle

Format I chose: `fact-` followed by 12 random hexadecimal characters
(`secrets.token_hex(6)`), for example `fact-3fa91c07b2d4`. Case handles use the
same scheme with the prefix `case-`.

A guessable handle would expose: other residents' data. With sequential
handles such as `fact-0007`, anyone who sees one handle knows how many facts
exist and can guess `fact-0006`, which is a read of somebody else's record.
A random handle has 48 bits of entropy, so it cannot be enumerated by guessing.

### 2. Conflict and retention

- A write that contradicts an older fact: keep both, because overwriting
  loses what changed and when. Each fact carries `written_at`, so a reader can
  tell which one is newer. The cost is that `recall` can return two
  contradictory facts and the caller has to cope with that.
- How long a record lives: until `forget(handle)` is called, because I did not
  implement any expiry. This is a deliberate simplification and would be wrong
  for a real service holding residents' data, where a retention period would
  be required. `forget` is a hard delete, and it does not reach anything
  already copied into a running conversation's messages: deleting the fact
  does not un-say it.

### 3. What k costs

k = 3. Tokens added per call: [à mesurer, estimation ci-dessous].

At four hundred facts in the store, this design stays cheap in tokens, because
`search` filters on the subject first and `k` caps what is returned, so the
context grows with k and not with the store. The scan itself is linear, which
is negligible at this size. What degrades is quality: with many facts for one
resident, keyword overlap ranks poorly and the right fact may not be in the
top 3, which is what week 7 fixes with embeddings.
### 4. Memory off against memory on

| | tokens | turns to finish |
| memory off | | |
| memory on | | |
how do i have those info ?
[The interesting result is usually that memory costs more tokens per call
and fewer calls per task. Whether that is a win depends on the task, and
saying which way it went for you is the entry.]

### 5. The protocol, at the wire

| server mode | status | Mcp-Session-Id | answered |
| stateless_http=True |200 |None |True |
| stateless_http=False |400 |present | false missing session ID|

The error the session-mode server returned, quoted exactly:

{"jsonrpc":"2.0","id":null,"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}

Why the two-server handle demonstration does not prove this on its own:

The old demonstration passed identically in both modes because the state was stored in a shared file and the client opened a fresh connection per call. It only proved that "a file is a file," whereas a real protocol test must fail when the stateless architecture/mode is switched off.

### 6. What forget does not reach

Deleting a fact removes it from the persistent database store, but it does not un-say it in ongoing conversations where the information has already been retrieved and written into the active message history or context window. For a resident, this means that simply calling forget is not enough to purge sensitive data if it has already been read into an active dialogue session or log file—both the persistent storage and the active conversation history must be cleared or truncated.

### Deferred

[Anything you did not get to, and why.]
