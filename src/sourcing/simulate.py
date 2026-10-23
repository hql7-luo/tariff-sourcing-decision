"""Monte Carlo simulation: re-run the model many times with uncertain inputs."""

import numpy as np
import pandas as pd

from .inputs import build_sites
from .model import OPTIONS, option_present_value, pv_to_unit_cost

# Uncertain inputs as triangular distributions: (low, most likely, high).
# Ranges are judgment calls anchored on the sourced base values in data/inputs.csv.
UNCERTAIN_INPUTS = {
    # Shanghai-LA spot was 3,132 in Jan 2026 and 7,884 in Oct 2026 (Drewry WCI)
    "ocean_cn_usd_per_feu": (3132, 5500, 8500),
    # China white cardboard moved about +/-15% over the past year
    "cn_board_cny_per_t_incl_vat": (3434, 4040, 4646),
    # North American board: cheaper Latin American supply (-20%) to further increases (+10%)
    "us_fbb_usd_per_t": (940, 1178, 1300),
    # A stronger yuan makes China more expensive in dollars
    "fx_cny_per_usd": (6.30, 6.6861, 7.10),
    # How fast new sites reach China-level output per hour
    "vn_productivity": (0.70, 0.80, 0.90),
    "mx_productivity": (0.75, 0.85, 0.95),
    # Mexico's 40-hour week reform could lift loaded labor cost by up to 20%
    "mx_wage_usd_per_hour_loaded": (5.00, 5.50, 6.60),
    # Used equipment (low) to overruns (high)
    "capex_usd": (3000000, 5000000, 6500000),
}


# Draw one set of inputs: the base inputs with each uncertain value replaced
def draw_inputs(base, rng):
    drawn = dict(base)
    for key, (low, mode, high) in UNCERTAIN_INPUTS.items():
        drawn[key] = rng.triangular(low, mode, high)
    return drawn


def run_monte_carlo(base, scenarios, n_draws=10000, seed=2026):
    rng = np.random.default_rng(seed)
    probabilities = [s["probability"] for s in scenarios]

    rows = []
    for draw in range(n_draws):
        inp = draw_inputs(base, rng)
        scenario = scenarios[rng.choice(len(scenarios), p=probabilities)]
        sites = build_sites(inp)

        row = {"draw": draw, "scenario": scenario["name"]}
        for option in OPTIONS:
            pv = option_present_value(option, scenario["tariff"], sites, inp)
            row[option] = pv_to_unit_cost(pv, inp)
        rows.append(row)

    results = pd.DataFrame(rows)
    results["cheapest"] = results[list(OPTIONS)].idxmin(axis=1)
    return results


# Per strategy: average cost, the P10-P90 range, how often it is the cheapest,
# and the "cost of being wrong" (extra cost versus the best choice in hindsight).
def summarize(results):
    best_in_hindsight = results[list(OPTIONS)].min(axis=1)
    summary = []
    for option, label in OPTIONS.items():
        values = results[option]
        regret = values - best_in_hindsight
        summary.append({
            "option": option,
            "label": label,
            "mean": values.mean(),
            "p10": values.quantile(0.10),
            "p50": values.quantile(0.50),
            "p90": values.quantile(0.90),
            "share_cheapest": (results["cheapest"] == option).mean(),
            "regret_mean": regret.mean(),
            "regret_p90": regret.quantile(0.90),
        })
    return pd.DataFrame(summary)
