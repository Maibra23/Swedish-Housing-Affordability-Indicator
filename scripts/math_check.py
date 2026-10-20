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
    "income": 400_500,           # Stockholms län 2024, county median income
    "transaction_price_sek": 6_748_000,
    "mortgage_rate": 4.30,       # mean on new mortgages, all fixation periods
    "year": 2024,
}
loan_per_income = 0.85 * baseline["transaction_price_sek"] / (2 * baseline["income"])

# Test 1: baseline (zero shocks) against the formula written out
r0 = simulate("01", 0, 0, 0, baseline)
by_hand = 100 * loan_per_income * (0.0430 * 0.7 + 0.02)
print(f"Baseline SHAI:        {r0['baseline_v_c']:.2f} % of income (by hand {by_hand:.2f})")
assert abs(r0["baseline_v_c"] - by_hand) < 1e-9, "Simulator disagrees with the written formula"
assert abs(r0["delta"]) < 0.001, "Zero shock should give zero delta"
print("VALIDATION PASSED: baseline matches the formula, zero shock -> zero delta")
print()

# Test 2: +2 pp moves only the interest term, by 2 x 0.7 % of the loan
r2 = simulate("01", 2.0, 0, 0, baseline)
expected = 100 * loan_per_income * 0.02 * 0.7
print(f"+2 pp rate: {r2['baseline_v_c']:.2f} -> {r2['scenario_v_c']:.2f} ({r2['delta_pct']:+.1f} %)")
assert abs(r2["delta"] - expected) < 1e-9, "Rate shock is not the interest term alone"
print("VALIDATION PASSED: a rate shock adds 0.7 x shock x loan / income")
print()

# Test 3: the 2021-23 cycle at annual means (+3.0 pp, +9 % income, -5 % price)
r_cycle = simulate("01", 3.0, 0.09, -0.05, baseline)
print(f"2021-23 cycle: {r_cycle['baseline_v_c']:.2f} -> {r_cycle['scenario_v_c']:.2f} ({r_cycle['delta_pct']:+.1f} %)")
assert r_cycle["delta"] > 0, "The rate cycle should raise the cost share"
print("VALIDATION PASSED: the 2021-23 cycle raises the cost, as households experienced")
print()

print("ALL MATH CHECKS PASSED")
