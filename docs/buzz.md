# Kaitersberg over Buzz

[Buzz](https://buzz.xyz) is Block's chat workspace where agents are channel
members. Put it in front of Kaitersberg and the pipeline gets a room: a channel
per product, a planner agent you brief in chat, a builder agent that runs the
delivery loop headless, and a status page in the channel canvas that refreshes
itself when a loop ends. Nothing about the pipeline changes - the skills, the
board, the rungs and the documents stay exactly what they are. Buzz only changes
where you stand while they run.

Why this works at all: Buzz agents are not bots with their own runtime. The
desktop app drives a real Claude Code process over the Agent Client Protocol
(`buzz-acp` spawns it as a subprocess), on a machine you choose. That process
sees the machine's filesystem and the machine's installed plugins - so an agent
whose host has the kaitersberg plugin installed has every `kaitersberg:*` skill,
with no Buzz-side porting.

## The shape

| Piece | What it is | Why |
|---|---|---|
| One channel per product | e.g. `#demo-product` | The channel is the project room and the permission boundary; agents are added to it like people |
| **Planner** agent | Claude Code harness, planning skills only | Briefing → spec → design → tasks, conversationally, in the channel |
| **Builder** agent | Claude Code harness | Starts `loop-feature.sh` detached in tmux and reports; refreshes the status canvas when asked |
| `status-canvas` workflow | Webhook-triggered, one `send_message` step | The loop's last act is a `curl`; the workflow @mentions the Builder, who writes `/status` output to the channel canvas |
| Product repo | a checkout the agents' machine can reach (the Buzz nest suggests `~/.buzz/REPOS/<product>`) | Both agents work in the same checkout; the board on the default branch coordinates them, as always |

Two design decisions worth keeping:

- **The delivery loop never runs inside an agent's chat turn.** A Buzz agent is
  one long-lived session, and `/review` requires a fresh one. `loop-feature.sh`
  already solves this - every stage is its own `claude -p` process - so the
  Builder's only job is to start it detached (`tmux new -d`) and narrate. An
  agent turn that ran the loop inline would both violate the fresh-session rule
  and die at the harness turn timeout.
- **Status is a workflow, not a third agent.** Buzz workflows have no
  "run agent" action (only `send_message`, `send_dm`, `set_channel_topic`,
  `add_reaction`, `call_webhook`, `request_approval`, `delay`) - and they don't
  need one. A workflow message's `@Name` mentions are resolved by the relay into
  `p` tags, and a `p` tag is exactly what wakes an agent. The message is posted
  with the owner's authority, so it passes even a `respond-to: owner-only`
  agent. `/status` itself changes nothing and needs no judgement; a standing
  agent identity for it would be a cron job wearing a name tag.

## Data boundary

Buzz is optional, but using it moves information out of the product repository.
Feature names, statuses, findings, branch names and generated status pages may be
sent to the configured relay and become visible to channel members. Do not put
secrets, customer data or unnecessary personal data into prompts, workflow messages
or the status canvas. Before using a hosted relay, check its access controls,
retention, deletion and data-location terms against the product's own obligations.
For a self-hosted relay, its operator owns those decisions.

The webhook secret authorises only the configured workflow trigger. Keep it out of
the repository and rotate it when an agent prompt or host is retired. Kaitersberg
does not send anything to Buzz unless a user configures and starts this integration.

## Prerequisites

Once per machine that will host the agents:

- Buzz desktop app, signed into your relay, with the **Claude Code harness
  installed** (the "Install" button on the Claude Code card - it drops the ACP
  adapter that lets `buzz-acp` drive Claude Code).
- Claude Code with the kaitersberg plugin at **user scope** (step 0 of the
  pipeline) - agents inherit it.
- A kaitersberg checkout, for `scripts/loop-feature.sh`.
- `tmux` and `git`.

## The process

### 1. Channel and repo

Create the product channel in the desktop app. Put the product repo where the
agents' machine can reach it - inside the Buzz nest, `~/.buzz/REPOS/<product>`,
is the convention the agents already know. A fresh product starts as a bare
`git init`; `/plan-product` and `/scaffold` do the rest, same as ever.

### 2. The two agents

Create both in the desktop app (agent creation is owner-reviewed by design -
a CLI or an agent can only *draft* the form, you save it). Runtime: Claude Code.
Give the Planner a generous turn timeout - the default (~5 minutes) is shorter
than one honest `/write-spec`. The Builder can keep the default; its turns only
start tmux sessions and read logs.

**Planner** system prompt - substitute your paths:

```
You are the Kaitersberg planner for the <PRODUCT> project.
Always work in <REPO_PATH> - cd there before anything else.
Use only the kaitersberg planning skills: kaitersberg:plan-product,
kaitersberg:add-feature, kaitersberg:write-spec, kaitersberg:tech-design,
kaitersberg:tasks. Never build, review, or merge.
Where the documents are silent, ask in the channel instead of inventing behaviour.
After each skill run, report which rung the feature moved to on features/INDEX.md.
```

**Builder** system prompt:

```
You are the Kaitersberg build operator for the <PRODUCT> project.
The repo is <REPO_PATH>.
When asked to deliver a feature PROJ-x that is Ready, start the delivery loop detached:
  tmux new -d -s PROJ-x 'cd <REPO_PATH> && \
    STAGE_DONE_CMD="curl --fail-with-body -sS -o /dev/null -X POST <RELAY_URL>/hooks/<WORKFLOW_ID> -H \"X-Webhook-Secret: <SECRET>\"" \
    PR=0 ROUNDS=3 <KAITERSBERG_PATH>/scripts/loop-feature.sh PROJ-x \
    || curl --fail-with-body -sS -o /dev/null -X POST <RELAY_URL>/hooks/<WORKFLOW_ID> -H "X-Webhook-Secret: <SECRET>"'
then confirm it started and tell the channel how to follow: tail -f features/PROJ-x-*/loop.log.
The webhook fires the status-canvas workflow, which asks you to refresh the
channel canvas - when that request arrives, run the kaitersberg:status skill
in the repo and write the generated page to the channel canvas with buzz canvas set.
On status requests, read the feature's loop.log and documents and summarize.
Never run stages inline in your own session (review requires a fresh session -
the script owns that), and never run /merge.
```

`STAGE_DONE_CMD` is the loop script's per-stage notification hook: it runs after
every stage outcome has been persisted, so a Builder woken immediately by the
webhook reads the new state rather than the one before the transition. The canvas
refreshes after `/build`, `/review` and `/qa` instead of once at the end - and the
status page must refresh after a red stage too, especially then. The loop records
the transition and the hook's exit code as secret-free JSON events in `loop.log`;
the hook receives `FEATURE`, `RUN_ID`, `STAGE`, `OUTCOME`, `HEAD_SHA`, `NEXT_STAGE`
and `ACTION`. The `|| curl` behind the script covers the exits that never reach a
stage outcome (a held lock, an infrastructure failure); on a normal end the last
stage's hook has already fired. `PR=0` while the sandbox has no remote;
drop it once the repo does, and the loop's green end opens the pull request as
usual. `/merge` stays human, in a terminal, always.

### 3. The status workflow

Created once per channel, with the `buzz` CLI as the workspace owner:

```yaml
name: status-canvas
description: Status page for <PRODUCT> in the channel canvas, fired by the loop end
trigger:
  on: webhook
steps:
  - id: ask_builder
    action: send_message
    text: "@<Builder name> Please run the kaitersberg:status skill in <REPO_PATH>
      and write the generated page to this channel's canvas with buzz canvas set.
      Change nothing else."
```

```sh
buzz workflows create --channel <CHANNEL_UUID> --yaml "$(cat workflow.yaml)"
```

Saving a webhook workflow returns its `webhook_secret` - that secret and the
workflow id go into the Builder's `curl` line above. The secret can only fire
this one status refresh, so living in an agent prompt is acceptable; re-saving
the workflow rotates it. One workflow has exactly one trigger - if you also
want a daily page regardless of loop activity, add a second workflow with an
`on: schedule` trigger and the same step.

Test the wiring end to end before trusting it:

```sh
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  <RELAY_URL>/hooks/<WORKFLOW_ID> -H 'X-Webhook-Secret: <SECRET>'   # expect 202
```

then watch the channel: the mention appears, the Builder wakes, the canvas
updates.

### 4. Working in it

- Brief the Planner in the channel: `@Planner <one-paragraph briefing>` - then
  `/write-spec`, `/tech-design`, `/tasks` per feature, with your approvals in
  the thread where everyone sees them.
- Hand a `Ready` feature to the Builder: `@Builder deliver PROJ-3`. Follow along
  with `tail -f features/PROJ-3-*/loop.log`, or just wait for the canvas.
- The invariants hold unchanged: the board lives on the default branch, one
  feature directory per feature, `/review` and `/qa` fix nothing, and where the
  documents are silent the agents ask - now in a channel, where the question and
  the answer are visible to everyone.

## Debugging from the terminal

Run the doctor from the product repository. Its default mode changes nothing: it
checks the board, feature folder, persisted loop state, process, tmux session,
lock, event-log age and the last notification receipt, then names the first broken
link and the next action.

```sh
cd <REPO_PATH>
python3 <KAITERSBERG_PATH>/scripts/buzz-doctor.py
python3 <KAITERSBERG_PATH>/scripts/buzz-doctor.py PROJ-3
python3 <KAITERSBERG_PATH>/scripts/buzz-doctor.py PROJ-3 --follow
python3 <KAITERSBERG_PATH>/scripts/buzz-doctor.py PROJ-3 --json
```

Give it the public Buzz identifiers to include the channel, membership, workflow,
recent workflow runs and canvas in the same diagnosis. The normal `buzz` CLI
credentials (`BUZZ_RELAY_URL`, `BUZZ_PRIVATE_KEY` and, for an agent identity,
`BUZZ_AUTH_TAG`) still determine what the current identity may read.

```sh
BUZZ_CHANNEL_ID=<CHANNEL_UUID> \
BUZZ_WORKFLOW_ID=<WORKFLOW_ID> \
BUZZ_BUILDER='<Builder name>' \
python3 <KAITERSBERG_PATH>/scripts/buzz-doctor.py PROJ-3
```

Only the webhook probe is active. It posts once, so it creates a visible workflow
message and should wake the Builder. The secret is read from an environment
variable and is never printed or included in the JSON report:

```sh
BUZZ_WEBHOOK_SECRET=<SECRET> \
python3 <KAITERSBERG_PATH>/scripts/buzz-doctor.py PROJ-3 \
  --probe-webhook <RELAY_URL>/hooks/<WORKFLOW_ID>
```

Exit `0` means every inspected layer is healthy, `1` means the remaining blind
spots are warnings, and `2` means the doctor found a hard failure. `--follow`
refreshes until `ctrl-c`; it cannot be combined with the active probe, so one
command cannot accidentally fire the workflow repeatedly.

## Letting Claude Code set it up

The setup above is a one-time systems task, and a Claude Code session on the
host machine can do almost all of it - everything except the clicks Buzz
reserves for the owner. Paste this into a session on the machine that will host
the agents:

```
Set up Kaitersberg over Buzz for the product <PRODUCT>.
My relay is at <RELAY_URL> (ssh alias: <HOST>, if any). Verify, don't assume:
1. Check the relay is reachable and the Buzz desktop app, buzz CLI, tmux, and
   the kaitersberg plugin (user scope) are installed on this machine.
2. Create the product repo at ~/.buzz/REPOS/<product> (git init + README) if it
   doesn't exist.
3. Read docs/buzz.md in my kaitersberg checkout and prepare the Planner and
   Builder system prompts with my real paths substituted.
4. Create the status-canvas workflow via the buzz CLI, capture the webhook
   secret from the save response, and put it into the Builder prompt.
5. Test the webhook with curl (expect 202) and confirm the mention arrives in
   the channel.
6. For anything only I can do - installing the Claude Code harness card,
   creating the channel, saving the agents - give me the exact click list and
   paste-ready prompts, or prefill the forms with buzz agents draft-create.
Tell me what you verified at each step; don't invent values you didn't read.
```

Later prompt-only changes go the same way - for example, rewiring an existing
agent:

```
Update the Kaitersberg Builder agent's system prompt to fire the status-canvas
webhook when the loop ends. Use buzz agents draft-update so the change lands as
a prefilled form for me to review - don't edit app files directly.
```

Field notes from doing exactly this, so the next session doesn't rediscover
them:

- **The CLI signs as an identity.** `BUZZ_RELAY_URL` and `BUZZ_PRIVATE_KEY`
  (hex or nsec) are required; the *owner's public* key is not a private key, and
  a random key gets `403 relay_membership_required`. The desktop app keeps all
  identities in the macOS keychain under service `buzz-desktop`, account
  `secrets` - reading it pops a consent dialog, which is the owner approving.
- **Behind a TLS-terminating proxy, NIP-98 auth fails on the scheme** (`event
  has https://…, expected http://…`). Point the CLI at the scheme the relay
  itself sees - `http://<host>` - or fix forwarded-proto at the proxy.
- **`buzz agents draft-create` / `draft-update` are agent requests to the
  owner**: they require an agent identity (`BUZZ_PRIVATE_KEY` *and*
  `BUZZ_AUTH_TAG`), open a prefilled form in the owner's desktop app, and change
  nothing until the owner saves. That is the mechanism, not a limitation - agent
  identity stays owner-reviewed.
- **Workflows cannot run agents; mentions wake them.** The relay resolves
  `@Name` in a workflow message to `p` tags (multi-word names included,
  longest-match, case-insensitive), and agent wake is `p`-tag-gated. Plain text
  without a resolvable member name wakes no one.
- Manual refresh at any time: the same `curl`, or `buzz workflows trigger
  --workflow <id>`.
