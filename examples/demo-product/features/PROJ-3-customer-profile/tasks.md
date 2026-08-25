# PROJ-3 - Tasks
| # | Task | Layer | Batch | Size | Depends on | ACs | Writes | Status | Owner |
|---|---|---|---|---|---|---|---|---|---|
| PROJ-3-T1 | Profile columns and the address table exist with row-level security and a backfill | Data | B1 | M | - | enabling | - | Done | build-agent |
| PROJ-3-T2 | Provenance, formats and the region rule stand as pure functions | Rules | B1 | M | - | AC-12 | - | Done | build-agent |
| PROJ-3-T3 | List row, select, toast and dialog exist as building blocks | Surface | B1 | M | - | enabling | - | Done | build-agent |
| PROJ-3-T4 | A profile is read in one go and changed with a version check | Interfaces | B2 | M | T1, T2 | AC-3, AC-4 | - | Done | build-agent |
| PROJ-3-T5 | The profile page shows master data, sharing and the delete dialog | Surface | B2 | M | T3, T4 | AC-5, AC-9 | - | In Progress | build-agent |
| PROJ-3-T6 | Foreign profiles stay invisible under another tenant | Protection | B3 | S | T4 | AC-21, AC-22 | - | Open | - |
| PROJ-3-T7 | Versions documented, migration rehearsed from a fresh database, gate green | Closing | B3 | S | T5, T6 | enabling | - | Open | - |
