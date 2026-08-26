# Kaitersberg

Dieses Repository enthält ausschließlich das Kaitersberg: die
Claude-Skillquellen, den generierten Codex-Port, die Plugin-Pakete, beide
Marketplace-Kataloge und die Skripte, die sie synchron halten. Produktbriefings,
Planungsartefakte und Produktcode gehören in eigene Produktrepositories.

## Vor jeder Arbeit lesen

- `CLAUDE.md`
- `README.md`

Ihre Regeln haben für Skill-, Port-, Plugin- und Marketplace-Änderungen Vorrang.

## Struktur

- `.claude/skills/` ist die einzige Quelle der Skillinhalte.
- `.agents/skills/` ist der generierte Codex-Port.
- `plugins/claude/kaitersberg/skills/` ist das generierte Claude-Pluginpaket.
- `plugins/codex/kaitersberg/skills/` ist das generierte Codex-Pluginpaket.
- `.claude-plugin/marketplace.json` und `.agents/plugins/marketplace.json` verteilen die Pakete.
- `scripts/port-to-codex.py` erzeugt und prüft alle abgeleiteten Skillbäume.

## Regeln

- Generierte Skillbäume niemals direkt bearbeiten. Änderungen beginnen immer in `.claude/skills/`.
- Nach jeder Skilländerung `python3 scripts/port-to-codex.py` und danach `python3 scripts/port-to-codex.py --check` ausführen.
- Harness-Unterschiede einmal in `scripts/port-to-codex.py` abbilden, nicht in generierten Dateien nachpatchen.
- Plugin- und Marketplace-Manifeste für beide Hosts gemeinsam ändern und validieren.
- In diesem Repository weder `$kaitersberg:architecture`, `$kaitersberg:scaffold` noch Produktfeatures ausführen.
- Keine Produktbriefings, Produktplanungen, Produktkonfiguration oder Produktgeheimnisse hier ablegen.
- `.env.local` und echte Geheimnisse niemals lesen, schreiben oder committen.
- Nicht auf dem Hauptbranch entwickeln oder direkt dorthin pushen, auch nicht als
  Maintainer oder Administrator; Änderungen erhalten einen eigenen Branch und
  Worktree und gelangen ausschließlich über einen Pull Request mit GitHubs
  **Squash and merge** auf `main`. Dadurch bleiben Review und CI die verbindliche
  Integrationsgrenze, und GitHub erzeugt und signiert den einzelnen Commit auf
  `main`, sodass er als **Verified** ausgewiesen wird.
