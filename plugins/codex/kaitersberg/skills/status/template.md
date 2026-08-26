# Status page skeleton

One file: `docs/status.html`. Fill the placeholders, repeat the marked blocks per
feature, delete whole sections that have nothing in them. Do not restyle it - the
value of this page is that two runs a week apart look identical except for the
facts.

Headings shown in English - write them in the language of the project's documents.
Everything in `{{double braces}}` is a placeholder. They are braces and not angle
brackets on purpose: one left unfilled shows up on the page as `{{...}}` instead of
being swallowed silently by the browser.

**The design, in four sentences**, so a change can be judged against something:
the page is one column of text at reading width, and everything on it is either a
fact or a label for a fact. Hierarchy is size, weight and empty space; there are no
boxes drawn around things that are already separated by air. Colour appears only
where it means a state - grey is the resting position. There is one bar and no
other chart, no progress ring, and no icon that is an emoji - the bar exists
because "7 of 19" is easier to feel than to read. Nothing animates except a
single settle on load, and that is turned off for anyone who asked for less motion.

---

```html
<!doctype html>
<html lang="{{de|en - the documents' language}}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{Product}} - Status</title>
<style>
  :root {
    --bg: #fbfbfd;
    --surface: #ffffff;
    --ink: #1d1d1f;
    --ink-2: #6e6e73;
    --ink-3: #86868b;
    --line: rgba(0, 0, 0, .09);
    --accent: #0071e3;
    --ok: #1d7a3e;      --ok-bg: rgba(52, 199, 89, .13);
    --warn: #9a5c00;    --warn-bg: rgba(255, 159, 10, .15);
    --stop: #c22a20;    --stop-bg: rgba(255, 59, 48, .12);
    --idle: #6e6e73;    --idle-bg: rgba(120, 120, 128, .12);
    --shadow: 0 1px 2px rgba(0, 0, 0, .04), 0 8px 28px rgba(0, 0, 0, .05);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #000000; --surface: #1c1c1e; --ink: #f5f5f7; --ink-2: #a1a1a6;
      --ink-3: #8e8e93; --line: rgba(255, 255, 255, .13); --accent: #2997ff;
      --ok: #6be18a;   --ok-bg: rgba(48, 209, 88, .16);
      --warn: #ffb340; --warn-bg: rgba(255, 159, 10, .18);
      --stop: #ff6961; --stop-bg: rgba(255, 69, 58, .16);
      --idle: #a1a1a6; --idle-bg: rgba(120, 120, 128, .22);
      --shadow: none;
    }
  }
  * { box-sizing: border-box; }
  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 400 17px/1.53 -apple-system, BlinkMacSystemFont, "SF Pro Text",
          "Helvetica Neue", "Segoe UI", Roboto, sans-serif;
    letter-spacing: -.011em;
    -webkit-font-smoothing: antialiased;
  }
  main { max-width: 860px; margin: 0 auto; padding: 88px 24px 120px; }
  section { margin-top: 76px; }
  h1, h2, .figure { letter-spacing: -.026em; font-weight: 600; margin: 0; }
  h1 { font-size: clamp(38px, 6.4vw, 56px); line-height: 1.06; }
  h2 { font-size: 13px; font-weight: 600; letter-spacing: .02em;
       text-transform: uppercase; color: var(--ink-3); margin-bottom: 18px; }
  p { margin: 0; }

  .eyebrow { font-size: 15px; color: var(--accent); font-weight: 600; margin-bottom: 10px; }
  .lede { font-size: 21px; line-height: 1.4; color: var(--ink-2); margin-top: 18px;
          max-width: 34em; letter-spacing: -.014em; }
  .stamp { font-size: 14px; color: var(--ink-3); margin-top: 26px; }

  .figure { font-size: clamp(34px, 5.4vw, 46px); line-height: 1.1; }
  .figure span { color: var(--ink-3); }
  .bar { display: flex; gap: 3px; height: 8px; margin: 26px 0 14px; }
  .bar i { display: block; border-radius: 980px; background: var(--seg, var(--idle-bg)); }
  .bar i.done { --seg: var(--accent); }
  .bar i.open { --seg: var(--idle-bg); }
  .legend { display: flex; flex-wrap: wrap; gap: 20px; padding: 0; margin: 0;
            list-style: none; font-size: 14px; color: var(--ink-2); }

  .card {
    background: var(--surface); border: 1px solid var(--line); border-radius: 18px;
    padding: 22px 24px; box-shadow: var(--shadow); margin-bottom: 12px;
  }
  .card h3 { font-size: 19px; font-weight: 600; letter-spacing: -.018em; margin: 0; }
  .card p { color: var(--ink-2); font-size: 16px; margin-top: 6px; max-width: 46em; }
  .card .meta { font-size: 14px; color: var(--ink-3); margin-top: 12px; }

  .pill { display: inline-block; border-radius: 980px; padding: 4px 11px;
          font-size: 13px; font-weight: 600; letter-spacing: -.005em;
          background: var(--idle-bg); color: var(--idle); }
  .pill.ok { background: var(--ok-bg); color: var(--ok); }
  .pill.warn { background: var(--warn-bg); color: var(--warn); }
  .pill.stop { background: var(--stop-bg); color: var(--stop); }

  .rows { list-style: none; padding: 0; margin: 0; }
  .rows li { display: flex; gap: 16px; align-items: baseline; padding: 15px 2px;
             border-top: 1px solid var(--line); }
  .rows li:first-child { border-top: 0; }
  .rows .name { font-weight: 500; flex: 1 1 auto; }
  .rows .note { color: var(--ink-3); font-size: 15px; flex: 0 0 auto; }

  footer { margin-top: 92px; padding-top: 22px; border-top: 1px solid var(--line);
           font-size: 13px; color: var(--ink-3); }

  @media (prefers-reduced-motion: no-preference) {
    section, header { animation: rise .5s cubic-bezier(.32, .72, 0, 1) both; }
    section:nth-of-type(1) { animation-delay: .04s; }
    section:nth-of-type(2) { animation-delay: .08s; }
    section:nth-of-type(3) { animation-delay: .12s; }
    section:nth-of-type(4) { animation-delay: .16s; }
    section:nth-of-type(5) { animation-delay: .20s; }
    @keyframes rise { from { opacity: 0; transform: translateY(12px); } }
  }
</style>
</head>
<body>
<main>

  <header>
    <p class="eyebrow">Project status</p>
    <h1>{{Product}}</h1>
    <p class="lede">{{the one line from docs/PRD.md - what the product is for}}</p>
    <p class="stamp">As of {{date}} · {{n}} features · {{n}} waves</p>
  </header>

  <section>
    <h2>Where it stands</h2>
    <p class="figure">{{n}} done <span>of {{m}}</span></p>
    <!-- One <i> per feature, in board order: class "done" or "open". -->
    <div class="bar" role="img" aria-label="{{n}} of {{m}} features done">
      <i class="done" style="flex:1"></i>
      <i class="open" style="flex:1"></i>
    </div>
    <ul class="legend">
      <li>{{n}} done</li>
      <li>{{n}} in progress</li>
      <li>{{n}} not started</li>
    </ul>
  </section>

  <section>
    <h2>Waiting for a decision</h2>
    <!-- Repeat per item. Delete the whole section when there is nothing. -->
    <div class="card">
      <h3>{{Feature name}}</h3>
      <p>{{what is waiting, in one sentence a non-developer can act on}}</p>
      <p class="meta"><span class="pill warn">{{Needs approval | Findings open | Question unanswered}}</span> · since {{date}}</p>
    </div>
  </section>

  <section>
    <h2>Being built</h2>
    <!-- Repeat per feature that is In Progress or In Review. -->
    <div class="card">
      <h3>{{Feature name}}</h3>
      <p>{{the scope line from features/INDEX.md}}</p>
      <p class="meta"><span class="pill">{{status in plain words}}</span> · {{n}} days in this state{{, and the verdict from review.md or qa.md when there is one}}</p>
    </div>
  </section>

  <section>
    <h2>Next</h2>
    <ul class="rows">
      <!-- The next wave, in order. -->
      <li><span class="name">{{Feature name}}</span><span class="note">{{the scope line, shortened}}</span></li>
    </ul>
  </section>

  <section>
    <h2>Done</h2>
    <ul class="rows">
      <li><span class="name">{{Feature name}}</span><span class="note">{{date it was merged}}</span></li>
    </ul>
  </section>

  <footer>
    Generated from the project's own documents on {{date}}. Not edited by hand -
    the next run overwrites this page.
  </footer>

</main>
</body>
</html>
```

---

## The pills

| Class | Use it for |
|---|---|
| `pill` | A neutral state: being built, in review, waiting its turn |
| `pill ok` | Finished, or a verdict that came back clean |
| `pill warn` | Waiting for a person, or stalled longer than a week |
| `pill stop` | Sent back with findings, or an open critical bug |

Four states are enough. A fifth colour means the page has started explaining itself
instead of showing the facts.
