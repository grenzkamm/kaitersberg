# Security

## Supported versions

Security fixes land on `main`. Older plugin releases receive fixes only when a
maintainer explicitly marks them as supported in a release note; otherwise update
to the newest release before reporting a reproduction.

## What this repository is

Instructions that an AI agent reads and then acts on, plus a few scripts. There is
no hosted Kaitersberg service, and the default pipeline needs no network service
beyond the harness. Optional hooks and integrations transmit only when a user
configures and starts them.

## What it makes an agent do on your machine

Installing this plugin gives an agent workflows that run commands in your
repository. Read this before the first run:

- **`/scaffold` starts services and writes configuration.** It is the only skill
  allowed to, and it carries `disable-model-invocation` so that a model cannot
  decide to run it - a person has to.
- **`/build`, `/fix` and `/qa` run the project's own commands**: package managers,
  migrations, test suites, containers, and a browser for the walkthrough.
- **`scripts/loop-feature.sh` runs them unattended**, in sessions started with
  `--permission-mode acceptEdits` for writing stages and `dontAsk` for reading ones.
  A stage that needs a decision ends the run rather than guessing.
- **No skill ever writes `.env.local`** or prints a real secret into a document.
  Secrets are named in the design, and the values stay with you.

Treat it the way you would treat any script that runs in your checkout: read what
it does before you let it run without watching.

## Reporting something

Open an issue for anything that is not sensitive. For a vulnerability - a skill
that can be steered into exfiltrating a secret, for example - use GitHub's
[private vulnerability report](https://github.com/grenzkamm/kaitersberg/security/advisories/new).
Do not include the vulnerability in a public issue, discussion or pull request.

Include the affected skill or script, the smallest reproduction, the impact and any
known mitigation. Remove real credentials, customer data and private product
artefacts from the report. The maintainers will acknowledge the report, investigate
it and coordinate a fix and disclosure with the reporter. Please allow reasonable
time for a fix before public disclosure.
