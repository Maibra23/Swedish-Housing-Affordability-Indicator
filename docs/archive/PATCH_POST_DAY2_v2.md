# SHAI Patch v2 — Median Transaction Price Fix
## Replaces the K/T swap from PATCH_POST_DAY2.md

**Priority:** P0, blocks Day 3
**Estimated time:** 45 to 90 minutes including verification
**Replaces:** The K/T substitution guidance in PATCH_POST_DAY2.md. K/T was the wrong fix.

---

## Why this patch exists

Two previous attempts to define the Price variable in the affordability formulas failed:

1. `price_index` (1990=100) is a growth measure, not a level. Stockholm ranked most affordable.
2. `kt_ratio` is transaction price divided by assessed value, a markup measure. Stockholm ranked most affordable (even more so) because Stockholm has high assessed values, which lowers the markup.

Neither variable measures absolute price level. Neither is comparable across regions for affordability purposes.

**The correct variable is median transaction price in SEK**, available in the same SCB table (`FastprisSHRegionAr`) under content code `BO0501C2` ("Purchase price, average in 1 000 SEK"). This is a level, in SEK, directly comparable across regions.

---

## Step 1 — Mandatory sanity check BEFORE any code changes

**Do not skip this step.** Run the sanity check first and confirm the expected ordering before modifying `affordability.py`.

### Task 1.A — Inspect raw parquet for BO0501C2

Run this diagnostic script (create as `scripts/diagnose_price_variable.py`):

```python
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")

# Load raw BO0501 transaction price file
df = pd.read_parquet(RAW / "BO0501_kt_ratio.parquet")

print("Unique ContentsCode values in the raw pull:")
print(df["ContentsCode_code"].unique() if "ContentsCode_code" in df.columns else df["ContentsCode"].unique())
print()
print("Unique Fastighetstyp values:")
print(df["Fastighetstyp_code"].unique() if "Fastighetstyp_code" in df.columns else df["Fastighetstyp"].unique())
print()
print("Row count:", len(df))
print("Columns:", df.columns.tolist())
```

### Expected outcomes

**If BO0501C2 is present in the raw file:**
Skip to Task 1.B below.

**If only BO0501C4 (K/T) is present:**
The original extractor filtered to K/T only. You need to pull BO0501C2 separately. See Task 1.C.

### Task 1.B — Sanity check the levels (only if BO0501C2 present)

```python
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
df = pd.read_parquet(RAW / "BO0501_kt_ratio.parquet")

# Filter to average purchase price, permanent housing, 2024
cc_col = "ContentsCode_code" if "ContentsCode_code" in df.columns else "ContentsCode"
ft_col = "Fastighetstyp_code" if "Fastighetstyp_code" in df.columns else "Fastighetstyp"
region_col = "Region_code" if "Region_code" in df.columns else "Region"
time_col = "Tid_code" if "Tid_code" in df.columns else "Tid"

prices = df[
    (df[cc_col] == "BO0501C2")
    & (df[ft_col] == "220")  # permanent housing småhus
    & (df[time_col] == "2024")
].copy()

prices["value_mkr"] = prices["value"] / 1000  # value is in 1000 SEK, convert to MSEK

# Print 4 key counties
for code, name in [("01", "Stockholm"), ("14", "Västra Götaland"),
                    ("12", "Skåne"), ("25", "Norrbotten")]:
    county_rows = prices[prices[region_col] == code]
    if len(county_rows) > 0:
        print(f"{name:20} ({code}): {county_rows['value_mkr'].mean():.2f} MSEK")
    else:
        print(f"{name:20} ({code}): NOT FOUND")
```

### Expected ordering (must verify before proceeding)

```
Stockholm        (01): ~5.5 to 6.5 MSEK   ← highest
Västra Götaland  (14): ~3.5 to 4.5 MSEK
Skåne            (12): ~3.5 to 4.5 MSEK
Norrbotten       (25): ~1.5 to 2.2 MSEK   ← lowest
```

Stockholm must be roughly 3x Norrbotten. If this does not hold, **halt**. Do not proceed to Step 2. Report back what the actual numbers are.

### Task 1.C — Pull BO0501C2 if missing

If BO0501C2 is not in the raw file, add an extraction function to `src/data/scb_client.py`:

```python
def fetch_transaction_price() -> pd.DataFrame:
    """
    Fetch median transaction price in SEK from SCB BO0501.

    Table: BO/BO0501/BO0501B/FastprisSHRegionAr
    Content code: BO0501C2 (Purchase price, average in 1 000 SEK)
    Fastighetstyp: 220 (permanent small house)
    Granularity: annual, all 290 municipalities + 21 counties + national
    """
    url = "https://api.scb.se/OV0104/v1/doris/sv/ssd/BO/BO0501/BO0501B/FastprisSHRegionAr"

    query = {
        "query": [
            {"code": "ContentsCode", "selection":
             {"filter": "item", "values": ["BO0501C2"]}},
            {"code": "Fastighetstyp", "selection":
             {"filter": "item", "values": ["220"]}},
            # Region and Tid: all
        ],
        "response": {"format": "json"}
    }

    # Use same chunked request pattern as other SCB fetches
    # Save to data/raw/BO0501_transaction_price.parquet
    ...
```

Then rerun the sanity check in Task 1.B against the new file.

---

## Step 2 — Apply the code fix

**Only after Step 1 confirms expected ordering.**

### File: `src/data/build_panel.py`

Add transaction price to the panel merge. Pseudocode:

```python
# Load new parquet
df_price_sek = pd.read_parquet("data/raw/BO0501_transaction_price.parquet")
df_price_sek = df_price_sek.rename(columns={"value": "transaction_price_ksek"})
df_price_sek["transaction_price_sek"] = df_price_sek["transaction_price_ksek"] * 1000

# Handle Stockholm + Gotland combined code 08+09 split if applicable (same as price_index)

# Merge into panel on (region_code, year)
# For municipalities: if native transaction price exists use it,
# else fall back to county median (same pattern as K/T logic).
# Add has_native_price flag.
```

Panel columns to add:
- `transaction_price_sek` (float, SEK)
- `has_native_price` (bool, true if municipality has its own transaction price, false if using county fallback)

### File: `src/indices/affordability.py`

Replace all references to `kt_ratio` in the affordability formulas with `transaction_price_sek`. Keep `kt_ratio` in the panel as a descriptive variable but do not use it in the formulas.

```python
def compute_version_a(panel: pd.DataFrame) -> pd.Series:
    """
    Version A: Bank style affordability ratio.

    Price variable: median transaction price in SEK (BO0501C2).
    Not price_index (growth measure) or kt_ratio (markup measure).
    """
    return panel["median_income"] / (panel["transaction_price_sek"] * panel["policy_rate"])


def compute_version_b(panel: pd.DataFrame) -> pd.DataFrame:
    """
    Version B: Macro composite pressure index.
    P/I ratio uses transaction price in SEK.
    """
    panel = panel.copy()
    panel["p_over_i"] = panel["transaction_price_sek"] / panel["median_income"]
    z_pi = (panel["p_over_i"] - panel["p_over_i"].mean()) / panel["p_over_i"].std()
    z_r = (panel["policy_rate"] - panel["policy_rate"].mean()) / panel["policy_rate"].std()
    z_u = (panel["unemployment_rate"] - panel["unemployment_rate"].mean()) / panel["unemployment_rate"].std()
    z_pi_inflation = (panel["cpi_yoy_pct"] - panel["cpi_yoy_pct"].mean()) / panel["cpi_yoy_pct"].std()
    return 0.35 * z_pi + 0.25 * z_r + 0.20 * z_u + 0.20 * z_pi_inflation


def compute_version_c(panel: pd.DataFrame) -> pd.Series:
    """
    Version C: Real affordability. Primary formula.
    """
    real_rate = (panel["policy_rate"] - panel["cpi_yoy_pct"]).clip(lower=0.005)
    return panel["median_income"] / (panel["transaction_price_sek"] * real_rate)
```

### File: `tests/test_validation.py`

Update Check 3 expectations:

```python
def test_stockholm_worst_v_c():
    """
    Stockholm should rank among top 5 worst affordability under Version C
    when using transaction_price_sek (not price_index or kt_ratio).
    """
    ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
    latest_year = ranked["year"].max()
    stockholm = ranked[(ranked["lan_code"] == "01") & (ranked["year"] == latest_year)]

    # Stockholm is a single county row at county level, or many municipalities at municipal level
    # Use county level for this test
    county_ranking = ranked[ranked["year"] == latest_year].groupby("lan_code")["version_c"].mean()
    county_ranking_sorted = county_ranking.sort_values()  # worst = smallest V_C (inverted)

    top_5_worst = county_ranking_sorted.head(5).index.tolist()
    assert "01" in top_5_worst, (
        f"Stockholm (01) should be top 5 worst under V_C. "
        f"Actual top 5 worst: {top_5_worst}. "
        f"If this fails, check transaction_price_sek is populated correctly."
    )


def test_norrbotten_best_v_a():
    """Norrbotten should rank among top 5 best affordability under Version A."""
    ranked = pd.read_parquet("data/processed/affordability_ranked.parquet")
    latest_year = ranked["year"].max()
    county_ranking = ranked[ranked["year"] == latest_year].groupby("lan_code")["version_a"].mean()
    top_5_best = county_ranking.sort_values(ascending=False).head(5).index.tolist()
    assert "25" in top_5_best, (
        f"Norrbotten (25) should be top 5 best under V_A. Actual: {top_5_best}"
    )
```

### File: `src/kontantinsats/engine.py`

If already implemented with a `taxeringsvärde_proxy` hack, replace with direct transaction price:

```python
def apply_regime(transaction_price_sek, income_sek, rate, regime_key, savings_rate=0.10):
    """
    Compute kontantinsats requirements under a regulatory regime.

    Uses actual median transaction price in SEK, not K/T times proxy.
    """
    regime = REGIMES[regime_key]
    required_cash = transaction_price_sek * regime["min_down_pct"]
    loan_amount = transaction_price_sek - required_cash
    ltv = loan_amount / transaction_price_sek
    lti = loan_amount / income_sek

    # ... rest of logic unchanged
```

---

## Step 3 — Rerun the pipeline end to end

```bash
# 1. Rebuild panel with new price column
python -m src.data.build_panel

# 2. Recompute indices
python -m src.indices.affordability

# 3. Rerun rankings
python -m src.indices.normalize

# 4. Run validation suite
pytest tests/test_validation.py -v
```

All 6 validation checks must pass. If any fail, halt and investigate before Day 3.

---

## Step 4 — Documentation updates

### METHODOLOGY_v2.md section 2 variable register

Replace the K/T entry's role in the formulas with transaction price:

```markdown
| Variable | Symbol | Source | Table / Endpoint | Resolution | Frequency | Coverage |
|----------|--------|--------|------------------|------------|-----------|----------|
| Median transaction price | P_sek | SCB BO0501 | BO/BO0501/BO0501B/FastprisSHRegionAr (BO0501C2) | Municipal, county, national | Annual | 1981 to 2024 |
| K/T ratio (descriptive) | KT | SCB BO0501 | Same table (BO0501C4) | Municipal, county | Annual | 1981 to 2024 |
```

Note: K/T stays in the panel as a **descriptive** variable, displayed in the Metodologi page as a market indicator, but is not used in any affordability formula.

### METHODOLOGY_v2.md section 3 formulas

Change Price variable in all three formulas from KT to P_sek:

```
Affordability_A(i, t) = Income(i, t) / (P_sek(i, t) × Rate(t))
Risk_B(i, t)          = 0.35 × z(P_sek/I) + 0.25 × z(R) + 0.20 × z(U) + 0.20 × z(π)
Affordability_C(i, t) = Income(i, t) / (P_sek(i, t) × max(R(t) − π(t), 0.005))
```

### METHODOLOGY_v2.md subsection "Why transaction price, not price index or K/T"

Replace the earlier "Why K/T, not price index" subsection with:

```markdown
### Why median transaction price in SEK, not price index or K/T ratio

Three candidate Price variables exist in SCB BO0501:

1. **Fastighetsprisindex** (1990=100): growth index, measures rate of change
   since a base year. Not comparable across regions because two counties with
   identical index values can have different absolute price levels.

2. **Köpeskillingskoefficient (K/T)**: ratio of transaction price to assessed
   value. Measures markup, not level. Rural counties have higher K/T because
   their assessed values lag market values more than urban areas do.

3. **Median köpeskilling in SEK (BO0501C2)**: median transaction price in
   absolute SEK. Level measure, directly comparable across regions.

SHAI uses option 3. An earlier iteration tried options 1 and 2 and both
produced the counterintuitive result that Stockholm ranked most affordable.
Transaction price in SEK produces the expected ordering (Stockholm least
affordable, Norrbotten most affordable) because Stockholm's roughly 40 percent
income advantage over Norrbotten is dominated by roughly 200 percent higher
transaction prices.

K/T remains in the panel as a descriptive market indicator but does not
enter any affordability formula.
```

### DEVIATIONS.md new entry

```markdown
## D14 — Price variable: BO0501C2 (transaction price) instead of BO0501R5 (price index) or BO0501C4 (K/T) ⚠️

| | |
|---|---|
| Attempt 1 | price_index (growth measure). Stockholm ranked most affordable. Wrong direction. |
| Attempt 2 | kt_ratio (markup measure). Stockholm ranked most affordable. Wrong direction. |
| Resolution | transaction_price_sek (BO0501C2, level in absolute SEK). Stockholm ranks least affordable as expected. |
| Root cause | Neither price_index nor K/T is a price level suitable for cross regional comparison. Only BO0501C2 is a level. |
| Tasks affected | 2.2 (affordability.py uses transaction_price_sek), 2.4 (validation test updated), 3.3 (kontantinsats uses direct price not K/T × proxy), 5.5 (Metodologi page explains the three way choice) |
| Prevention rule | Any future variable substitution requires a sanity check printing raw values for Stockholm and Norrbotten before running full pipeline. See scripts/diagnose_price_variable.py pattern. |
```

---

## Step 5 — Checkpoint before Day 3

Do not start Task 3.1 until:

- [ ] Sanity check output shows Stockholm roughly 3x Norrbotten transaction price
- [ ] `transaction_price_sek` column is present in `panel_municipal.parquet` and `panel_county.parquet`
- [ ] `pytest tests/test_validation.py` passes all 6 checks
- [ ] Stockholm ranks in top 5 worst counties under Version C
- [ ] Norrbotten ranks in top 5 best counties under Version A
- [ ] METHODOLOGY_v2.md updated with the three way rationale
- [ ] DEVIATIONS.md updated with D14

If all six boxes check, you are unblocked. Start Task 3.1 with PROMPTS_v2.md unchanged.

---

## Rule for future variable questions

This is the third attempt at the price variable. The pattern that worked:

1. **Print raw values for two known cases** (Stockholm and Norrbotten) before touching the formula
2. **Verify the ordering matches domain expectation** (Stockholm prices ~3x Norrbotten)
3. **Only then** modify `affordability.py`

The pattern that failed twice: assume the variable is a level based on its name, swap it in, run validation, discover the ranking is wrong, hypothesize a cause. This inverts the debugging order and costs a correction cycle each time.

Apply this rule to any future variable question on this project.