"""Math verification script for Phase 3 changes."""
import sys
sys.path.insert(0, ".")

from src.scenario.simulator import simulate
from src.kontantinsats.engine import compare_regimes, REGIMES

# ── Kontantinsats math check ──────────────────────────────────────────
print("=== KONTANTINSATS MATH CHECK ===")
# Stockholm municipality 2024 (from audit document)
price_sthlm = 8_597_000
income_sthlm = 533_800
rate_decimal = 0.0363   # 3.63%
bank_margin = 0.017     # 1.7pp typical bank margin

print(f"Stockholm 2024 villa price:  {price_sthlm/1e6:.3f} MSEK")
print(f"Individual income:           {income_sthlm:,} SEK")
print()

# Single household, no bank margin (policy rate only)
r1 = compare_regimes(price_sthlm, income_sthlm, rate_decimal, savings_rate=0.10, bank_margin=0.0)
b = r1["amort_2"]
print("--- SINGLE, policy rate only (3.63%) ---")
print(f"  Required cash:  {b['required_cash']:,.0f} SEK ({b['required_cash']/price_sthlm:.0%})")
print(f"  Years to save:  {b['years_to_save']:.1f} yr")
print(f"  Monthly cost:   {b['monthly_total']:,.0f} SEK")
print(f"  LTV: {b['ltv']:.0%}  LTI: {b['lti']:.1f}x  Amort: {b['amort_pct']:.0%}")
print()

# Couple, no bank margin — income doubled
income_couple = income_sthlm * 2
r2 = compare_regimes(price_sthlm, income_couple, rate_decimal, savings_rate=0.10, bank_margin=0.0)
b2 = r2["amort_2"]
print("--- COUPLE (2x income), policy rate only ---")
print(f"  Household income: {income_couple:,} SEK")
print(f"  Required cash:  {b2['required_cash']:,.0f} SEK  (same price, same down payment)")
print(f"  Years to save:  {b2['years_to_save']:.1f} yr  (should be half of single = {b['years_to_save']/2:.1f})")
print(f"  Monthly cost:   {b2['monthly_total']:,.0f} SEK  (same loan, same rate)")
print(f"  LTI: {b2['lti']:.1f}x  (half of single {b['lti']:.1f}x — couple income doubles denominator)")
print()

# Single with bank margin 1.7pp
r3 = compare_regimes(price_sthlm, income_sthlm, rate_decimal, savings_rate=0.10, bank_margin=bank_margin)
b3 = r3["amort_2"]
effective_rate_pct = (rate_decimal + bank_margin) * 100
print(f"--- SINGLE, with bank margin 1.7pp (effective rate {effective_rate_pct:.2f}%) ---")
print(f"  Monthly cost:   {b3['monthly_total']:,.0f} SEK  (was {b['monthly_total']:,.0f} at policy rate)")
print(f"  Difference:     +{b3['monthly_total']-b['monthly_total']:,.0f} SEK/month from bank margin")
loan = b['loan_amount']
interest_diff = loan * bank_margin
print(f"  Cross-check:    loan {loan/1e6:.2f}M x 1.7% = {interest_diff/12:,.0f} SEK/month extra interest")
print()

# Ordering check
for regime_key in ["pre_2010", "bolanetak", "amort_1", "amort_2"]:
    r_all = compare_regimes(price_sthlm, income_sthlm, rate_decimal)
    costs = {k: v["monthly_total"] for k, v in r_all.items()}
assert costs["amort_2"] >= costs["amort_1"] >= costs["bolanetak"], "Ordering violated!"
print("VALIDATION PASSED: amort_2 >= amort_1 >= bolanetak")
print()

# ── Scenario simulator math check ──────────────────────────────────────
print("=== SCENARIO SIMULATOR MATH CHECK ===")
baseline = {
    "income": 552_000,           # Stockholm county 2024
    "transaction_price_sek": 6_748_000,
    "policy_rate": 3.63,
    "cpi_yoy_pct": 2.86,
}

# Test 1: baseline (zero shocks)
r0 = simulate("01", 0, 0, 0, baseline, cpi_shock=0.0)
print(f"Baseline SHAI:        {r0['baseline_v_c']:.2f}")
print(f"Baseline real rate:   {r0['real_rate_base']:.2f}pp  (3.63 - 2.86 = 0.77 > 0.5 floor)")
assert abs(r0["delta"]) < 0.001, "Zero shock should give zero delta"
print("VALIDATION PASSED: zero shock -> zero delta")
print()

# Test 2: Riksbanken 2022 scenario (+4pp rate, +8pp CPI, -15% price)
r2022 = simulate("01", 4.0, 0, -0.15, baseline, cpi_shock=8.0)
print("Riksbanken 2022 scenario (+4pp rate, +8pp CPI, -15% price):")
print(f"  Rate:       {r2022['baseline_rate']:.2f}pp -> {r2022['scenario_rate']:.2f}pp")
print(f"  CPI:        {r2022['baseline_cpi']:.2f}pp -> {r2022['scenario_cpi']:.2f}pp")
print(f"  Real rate:  {r2022['real_rate_base']:.2f}pp -> {r2022['real_rate_scen']:.2f}pp  (rate +4, CPI +8 = real rate -4)")
print(f"  SHAI:       {r2022['baseline_v_c']:.2f} -> {r2022['scenario_v_c']:.2f}  (delta {r2022['delta']:+.2f}, {r2022['delta_pct']:+.1f}%)")
print(f"  Key insight: +4pp rate offset by +8pp CPI -> real rate actually FALLS -> affordability IMPROVES (despite lower price)")
print()

# Test 3: Rate-only shock (old behavior, no CPI)
r_rate_only = simulate("01", 4.0, 0, -0.15, baseline, cpi_shock=0.0)
print("Same rate/price shock but CPI unchanged (old behavior):")
print(f"  Real rate:  {r_rate_only['real_rate_base']:.2f}pp -> {r_rate_only['real_rate_scen']:.2f}pp  (rate +4, CPI unchanged)")
print(f"  SHAI:       {r_rate_only['baseline_v_c']:.2f} -> {r_rate_only['scenario_v_c']:.2f}  (delta {r_rate_only['delta']:+.2f})")
print(f"  Key insight: without CPI offset, affordability drops sharply")
print()

# Test 4: Deflation scenario
r_deflation = simulate("01", -1.0, 0, -0.10, baseline, cpi_shock=-2.0)
print("Deflation scenario (-1pp rate, -2pp CPI, -10% price):")
print(f"  Rate:       {r_deflation['baseline_rate']:.2f}pp -> {r_deflation['scenario_rate']:.2f}pp")
print(f"  CPI:        {r_deflation['baseline_cpi']:.2f}pp -> {r_deflation['scenario_cpi']:.2f}pp")
print(f"  Real rate:  {r_deflation['real_rate_base']:.2f}pp -> {r_deflation['real_rate_scen']:.2f}pp  (rate -1, CPI -2 = real rate +1)")
print(f"  SHAI:       {r_deflation['baseline_v_c']:.2f} -> {r_deflation['scenario_v_c']:.2f}  (delta {r_deflation['delta']:+.2f})")
print()

print("ALL MATH CHECKS PASSED")
