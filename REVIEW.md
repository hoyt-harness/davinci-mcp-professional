# Code Review Notes — davinci-mcp-professional

## What failure looks like here
A tool handler returns a success result when the underlying Resolve API call
silently failed — usually a stale FusionScript handle or a None return that
wasn't checked before use.

## Key invariants the reviewer should check
- Every domain handler checks for None before using the Resolve client object
- `auto-recovery` path (stale handle → disconnect → reconnect) is exercised in tests
- DAVINCI_MCP_DOMAINS startup pre-activation doesn't suppress activation errors
- Tool argument validation rejects invalid types before passing to the Resolve API
- No hard-coded version numbers in user-facing docs (use git tags)

## Paths to skip
- `var/` — health reports, not source
- `etc/` — probe scripts, not production code

## Finding standards
- Every finding must cite a specific file and line number
- Cap nits at 3 per review pass; flag the class, not every instance
