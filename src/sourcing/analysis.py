"""Analysis built on the cost model: scenario table, thresholds, sensitivity and the decision map."""

import pandas as pd

from .inputs import build_sites
from .model import (COMPONENTS, OPTIONS, landed_cost, option_present_value,
                    pv_to_unit_cost, site_investment)

SITE_CODES = ["CN", "VN", "MX"]


# Cost breakdown per 1,000 cartons for each site: ramp-up year, steady state,
# and the 5-year average (present-value weighted, so it matches the 5-year totals)
def cost_breakdown(inp, tariffs):
    sites = build_sites(inp)
    rate = inp["discount_rate"]
    horizon = int(inp["horizon_years"])
    weights = [1 / (1 + rate) ** year for year in range(1, horizon + 1)]

    rows = []
    for code in SITE_CODES:
        site = sites[code]
        investment = site_investment(site, inp)
        yearly = [landed_cost(site, tariffs[code], year, investment, inp) for year in range(1, horizon + 1)]

        periods = {"year 1": yearly[0], "steady state": yearly[1]}
        periods["5-year average"] = {
            c: sum(w * cost[c] for w, cost in zip(weights, yearly)) / sum(weights)
            for c in COMPONENTS + ["total"]
        }
        for period, cost in periods.items():
            row = {"site": site["name"], "period": period}
            row.update({c: cost[c] for c in COMPONENTS})
            row["total"] = cost["total"]
            rows.append(row)
    return pd.DataFrame(rows)


# Every strategy under every tariff scenario, with base-case inputs
def scenario_table(inp, scenarios):
    sites = build_sites(inp)
    rows = []
    for scenario in scenarios:
        for option, label in OPTIONS.items():
            pv = option_present_value(option, scenario["tariff"], sites, inp)
            rows.append({
                "scenario": scenario["name"],
                "scenario_label": scenario["label"],
                "probability": scenario["probability"],
                "option": option,
                "label": label,
                "pv_usd_millions": pv / 1e6,
                "avg_cost_per_k": pv_to_unit_cost(pv, inp),
            })
    table = pd.DataFrame(rows)

    # Probability-weighted average across scenarios
    weighted = (table.assign(w=table["avg_cost_per_k"] * table["probability"])
                .groupby(["option", "label"], sort=False)["w"].sum().reset_index()
                .rename(columns={"w": "avg_cost_per_k"}))
    weighted["scenario"] = "expected"
    weighted["scenario_label"] = "Probability-weighted"
    return table, weighted


# Value of `x` where a straight-line function f crosses zero (two-point solve)
def solve_linear(f, x0=0.0, x1=1.0):
    y0, y1 = f(x0), f(x1)
    return x0 - y0 * (x1 - x0) / (y1 - y0)


# Thresholds that would change the decision (5-year view, ramp-up included)
def thresholds(inp, scenarios):
    sites = build_sites(inp)
    today = next(s for s in scenarios if s["name"] == "status_quo")["tariff"]

    def gap_vs_china(option, cn_tariff):
        tariffs = dict(today, CN=cn_tariff)
        return (option_present_value("china", tariffs, sites, inp)
                - option_present_value(option, tariffs, sites, inp))

    cn_vs_vn = solve_linear(lambda t: gap_vs_china("vietnam", t))
    cn_vs_mx = solve_linear(lambda t: gap_vs_china("mexico", t))

    # Mexico: the delivered board price that would make Mexico match China today
    china_pv = option_present_value("china", today, sites, inp)

    def mexico_gap(board_price):
        changed = dict(inp, us_fbb_usd_per_t=board_price / (1 + inp["mx_board_delivery_uplift"]))
        return option_present_value("mexico", today, build_sites(changed), changed) - china_pv

    mx_board = solve_linear(mexico_gap, 500.0, 1500.0)

    return pd.DataFrame([
        {"threshold": "China tariff at which Vietnam matches China (Vietnam at 12.5%)",
         "value": cn_vs_vn, "today": today["CN"], "unit": "tariff rate"},
        {"threshold": "China tariff at which Mexico matches China (Mexico USMCA 0%)",
         "value": cn_vs_mx, "today": today["CN"], "unit": "tariff rate"},
        {"threshold": "Delivered board price at which Mexico matches China",
         "value": mx_board, "today": sites["MX"]["board_usd_per_t"], "unit": "USD per tonne"},
    ])


# Tornado data: how much each driver moves the 5-year gap (Vietnam minus China).
# Negative gap = Vietnam is cheaper.
def sensitivity(inp, scenarios):
    today = next(s for s in scenarios if s["name"] == "status_quo")["tariff"]

    def gap(changed_inp, tariffs):
        sites = build_sites(changed_inp)
        vn = option_present_value("vietnam", tariffs, sites, changed_inp)
        cn = option_present_value("china", tariffs, sites, changed_inp)
        return pv_to_unit_cost(vn - cn, changed_inp)

    base = gap(inp, today)
    board = inp["cn_board_cny_per_t_incl_vat"]
    drivers = [
        # (label, input key or tariff code, low value, high value)
        ("China tariff: 25% to 62.5%", "tariff:CN", 0.25, 0.625),
        ("Vietnam tariff: 0% to 22.5%", "tariff:VN", 0.0, 0.225),
        ("Years to recover the plant: 3 to 8", "horizon_years", 3, 8),
        ("Plant investment: $3.0M to $6.5M", "capex_usd", 3.0e6, 6.5e6),
        ("Vietnam output per hour: 70% to 90% of China", "vn_productivity", 0.70, 0.90),
        ("Vietnam wages: -20% to +20%", "vn_wage_vnd_per_month",
         inp["vn_wage_vnd_per_month"] * 0.8, inp["vn_wage_vnd_per_month"] * 1.2),
        ("China wages: -20% to +20%", "cn_wage_cny_per_year",
         inp["cn_wage_cny_per_year"] * 0.8, inp["cn_wage_cny_per_year"] * 1.2),
        ("Yuan per USD: 6.30 to 7.10", "fx_cny_per_usd", 6.30, 7.10),
        ("Vietnam site overhead: -25% to +25%", "vn_site_admin_usd_per_year",
         inp["vn_site_admin_usd_per_year"] * 0.75, inp["vn_site_admin_usd_per_year"] * 1.25),
        ("China board price: -15% to +15%", "cn_board_cny_per_t_incl_vat", board * 0.85, board * 1.15),
        ("Ocean freight: $3,132 to $8,500 per container", "ocean_cn_usd_per_feu", 3132, 8500),
    ]

    rows = []
    for label, key, low, high in drivers:
        results = []
        for value in (low, high):
            changed_inp = dict(inp)
            tariffs = dict(today)
            if key.startswith("tariff:"):
                tariffs[key.split(":")[1]] = value
            else:
                changed_inp[key] = value
            results.append(gap(changed_inp, tariffs))
        rows.append({"driver": label, "gap_at_low": results[0], "gap_at_high": results[1],
                     "base_gap": base, "swing": abs(results[1] - results[0])})
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


# Decision map: the lines in (China tariff, Vietnam tariff) space where the cheapest
# "move now" option changes, with Mexico at its USMCA rate of 0%.
# Every 5-year cost is a straight line in the tariff rates, so each boundary is straight too.
def decision_boundaries(inp):
    sites = build_sites(inp)

    def pv(option, cn, vn):
        return option_present_value(option, {"CN": cn, "VN": vn, "MX": 0.0}, sites, inp)

    # China = Vietnam: China tariff that breaks even, at two Vietnam tariff levels
    def china_vs_vietnam(vn):
        return solve_linear(lambda cn: pv("china", cn, vn) - pv("vietnam", cn, vn))

    vn_low, vn_high = 0.0, 0.40
    cn_at_low, cn_at_high = china_vs_vietnam(vn_low), china_vs_vietnam(vn_high)

    # China = Mexico (does not depend on Vietnam) and Vietnam = Mexico (does not depend on China)
    cn_vs_mx = solve_linear(lambda cn: pv("china", cn, 0.0) - pv("mexico", cn, 0.0))
    vn_vs_mx = solve_linear(lambda vn: pv("vietnam", 0.0, vn) - pv("mexico", 0.0, vn))

    return {
        "china_vietnam_line": [(cn_at_low, vn_low), (cn_at_high, vn_high)],
        "china_mexico_tariff": cn_vs_mx,
        "vietnam_mexico_tariff": vn_vs_mx,
    }


# China tariff on the China = Vietnam boundary for a given Vietnam tariff
def china_vietnam_boundary(boundaries, vn):
    (x0, y0), (x1, y1) = boundaries["china_vietnam_line"]
    return x0 + (vn - y0) * (x1 - x0) / (y1 - y0)
