# demo-product

Invented data, used to photograph `scripts/loop-dashboard.py` for the README and to
try the dashboard without pointing it at anybody's real project. Nothing here was
produced by the pipeline; it is written to look like what the pipeline produces.

```bash
cd examples/demo-product && python3 ../../scripts/loop-dashboard.py
```

The read-only API is available from the same process. For example:

```bash
curl http://localhost:8787/api/v1/snapshot | jq .
```
