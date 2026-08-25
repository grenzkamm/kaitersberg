# PROJ-4 - Tasks
| # | Task | Layer | Batch | Size | Depends on | ACs | Writes | Status | Owner |
|---|---|---|---|---|---|---|---|---|---|
| PROJ-4-T1 | Documents are stored, listed and removed, one owner per tenant | Data | B1 | M | - | AC-1, AC-2 | - | Done | build-agent |
| PROJ-4-T2 | Upload accepts the documented types and refuses the rest with the spec's wording | Interfaces | B1 | M | - | AC-3, AC-8 | - | Done | build-agent |
| PROJ-4-T3 | The library page lists, filters and opens a document | Surface | B2 | M | T1, T2 | AC-4, AC-5 | - | In Progress | build-agent |
| PROJ-4-T4 | A document of another tenant is invisible and cannot be opened by id | Protection | B2 | S | T1 | AC-11, AC-12 | - | Open | - |
