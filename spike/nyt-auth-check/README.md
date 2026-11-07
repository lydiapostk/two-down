# Spike: NYT puzzle retrieval without authentication material

**Status:** Result not yet recorded

## Question

Can the existing Python NYT puzzle integration retrieve puzzle data without sending authentication-bypass headers, session cookies, or other authenticated credentials?

## Scope

Test the existing Python retrieval code with no manually supplied bypass headers or cookies. Record whether the request succeeds, the response status, and which puzzle data is returned. This experiment does not establish that access is authorized for every puzzle or that the endpoint is stable.

## Reproduce

From the directory containing `spike.py`, activate the Python environment and install the spike's dependencies if needed. Then run both commands:

```bash
python spike.py shape
python spike.py fetch
```

These are the original commands used for the experiment. The precise behavior of the `shape` and `fetch` subcommands should be documented from the script or its output; do not assume that either command establishes successful unauthenticated retrieval on its own.

## Test conditions

- No session cookies supplied explicitly.
- No manually added authentication-bypass headers.
- Record whether the Python library adds any default headers or uses ambient credentials automatically.
- Do not commit credentials, cookies, tokens, or response bodies containing secrets.

## Results

- **Date tested:** TODO
- **Script / command:** `python spike.py shape` and `python spike.py fetch`
- **Puzzle / endpoint tested:** TODO
- **HTTP status:** TODO
- **Puzzle data retrieved:** TODO
- **Unexpected headers or cookies observed:** TODO
- **Conclusion:** TODO — success, failure, or inconclusive

## Next steps

Document the observed behavior and decide whether this retrieval method is suitable for the Python API. Recheck if NYT changes its endpoint or access requirements.
