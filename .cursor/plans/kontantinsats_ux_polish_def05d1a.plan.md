---
name: Kontantinsats UX Polish
overview: "Fix readability issues across the entire Kontantinsats page: simplify regime card values, add sparkvot tooltip/context, fix chart annotation overlap, explain Tillganglighet/Otillganglig, and fix a real amortization engine bug where LTV-based rules are not cumulative as documented."
todos:
  - id: sparkvot-tooltip-context
    content: Add help text to sparkvot slider and a dynamic SEK caption below it
    status: pending
  - id: simplify-regime-deltas
    content: Round large deltas to tkr, hide zero deltas, and add pre_2010 caveat note
    status: pending
  - id: explain-tillganglighet
    content: Expand the Tillganglighet KPI tooltip with threshold definitions
    status: pending
  - id: fix-chart-annotations
    content: Fix reference line annotation positioning to avoid overlap with bar text
    status: pending
  - id: tabs-usage-hint
    content: Add usage hint caption above the tabbed comparison section
    status: pending
  - id: verify-all
    content: "Run pytest and visual check: sparkvot context, card readability, chart labels, tooltips"
    status: pending
isProject: false
---

# Kontantinsats UX polish and assumption audit

## Assumption audit findings (engine logic)

After reviewing [`src/kontantinsats/engine.py`](src/kontantinsats/engine.py) lines 101-108, I found a real bug in the amortization calculation:

```python
for rule in regime["amort_rules"]:
    if "ltv_threshold" in rule and ltv > rule["ltv_threshold"]:
        amort_pct = max(amort_pct, rule["amort_pct"])   # <-- takes MAX, not cumulative
    if "lti_threshold" in rule and lti > rule["lti_threshold"]:
        amort_pct += rule["amort_pct"]                   # <-- adds (correct for LTI)
```

**Problem**: For `amort_1` and `amort_2`, the LTV-based rules should be cumulative tiers per Finansinspektionen's actual regulation:
- LTV > 70%: 2% amortization
- LTV > 50% (but <= 70%): 1% amortization

The `max()` logic means if LTV > 70%, it takes `max(0.02, 0.01) = 0.02` -- which happens to be correct for that specific case. But consider: if someone has LTV = 60% (between 50% and 70%), they should pay 1%, and the code gives 1% (correct). If LTV = 75%, they should pay 2% (the higher tier replaces the lower), and the code gives 2% (correct via max). So the `max()` logic actually **works correctly** because these are tiered thresholds (not additive bands). The LTI rule IS additive on top (correct).

**Verdict**: The engine is correct for the standard interpretation of the rules. No code change needed.

However, the `pre_2010` regime showing **0 SEK kontantinsats** and **0 years to save** is technically correct (no formal minimum) but misleading -- in practice most banks still required some equity. This is a presentation/communication issue, not a bug.

---

## Changes to [`pages/04_Kontantinsats.py`](pages/04_Kontantinsats.py)

### 1. Sparkvot slider: add tooltip and context (lines 74-82)

Add `help=` parameter to the slider explaining what sparkvot means and showing the SEK amount it represents:

```python
savings_rate = st.slider(
    "Sparkvot (%)",
    min_value=5, max_value=25, value=10, step=1,
    key="ki_savings_slider",
    help="Andel av bruttoinkomsten som sparas årligen. 10% ar vanligt; "
         "over 20% ar ambitionst. Paverkar hur lang tid det tar att spara ihop insatsen.",
) / 100.0
```

Add a dynamic caption below the slider showing the concrete SEK amount:

```python
st.caption(f"= {format_sek(income * savings_rate)} SEK/ar i sparande")
```

### 2. Regime cards: simplify value display (lines 243-293)

Current values like `-500 850 SEK` and `+0 SEK` are hard to parse. Changes:

- **Round deltas to nearest thousand** (tkr) for values above 10 000 SEK -- e.g. show `-501 tkr` instead of `-500 850 SEK`
- **Hide zero deltas** -- if delta is 0, show nothing (rather than `+0 SEK` / `+0,0 ar`)
- **Add a caveat note** under the `pre_2010` card noting that "i praktiken kravde banker ofta 5-10 % eget kapital" (in practice banks often required 5-10%)

### 3. Tillganglighet KPI: explain "Otillganglig" (lines 106-142)

The current tooltip just says "Baserat pa sparar under nuvarande regler." -- users don't understand the thresholds. Change the tooltip and add threshold context:

```python
tooltip=(
    "Tillganglig = under 5 ars spartid. "
    "Anstrangd = 5-10 ar. "
    "Otillganglig = over 10 ar spartid vid vald sparkvot."
),
```

### 4. Chart reference lines: fix overlap (lines 296-454)

The `annotation_position="top right"` causes labels to overlap bar text. Changes:

- Move annotations to `"bottom left"` for reference lines that are above the bars
- Add `annotation_font_color=COLORS["text_secondary"]` for subtler appearance
- For the "Ar att spara" tab with two ref lines at y=5 and y=10, stagger positions: one `"top left"`, one `"bottom right"`

### 5. Tabbed section: add usage hint (lines 354-357)

Add a small instruction caption above the tabs:

```python
st.caption("Valj flik for att jamnfora regelverken fran olika perspektiv. "
           "Andra ar i sidopanelen for att se historiska scenarion.")
```

### 6. Pre-2010 caveat in regime cards (section 5, inside the loop)

For the `pre_2010` key only, after the metrics, add:

```python
if key == "pre_2010":
    st.caption("Obs: Inget formellt insatskrav, men banker kravde ofta 5-10 %.")
```

---

## Files changed

- [`pages/04_Kontantinsats.py`](pages/04_Kontantinsats.py) -- all UI changes above
- No changes to [`src/kontantinsats/engine.py`](src/kontantinsats/engine.py) -- engine logic confirmed correct
- No changes to [`src/ui/components.py`](src/ui/components.py) or [`src/ui/css.py`](src/ui/css.py)
