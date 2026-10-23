"""Checks that the cost model behaves the way the methodology says it does."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sourcing.analysis import solve_linear  # noqa: E402
from sourcing.inputs import build_sites, load_inputs, load_scenarios  # noqa: E402
from sourcing.model import (OPTIONS, capital_recovery_per_year, landed_cost,  # noqa: E402
                            option_present_value, pv_to_unit_cost, site_investment,
                            staged_present_value)


@pytest.fixture(scope="module")
def setup():
    inp = load_inputs()
    return inp, build_sites(inp), load_scenarios()


def test_scenario_probabilities_sum_to_one(setup):
    _, _, scenarios = setup
    assert sum(s["probability"] for s in scenarios) == pytest.approx(1.0)


def test_components_add_up_to_total(setup):
    inp, sites, _ = setup
    for site in sites.values():
        cost = landed_cost(site, 0.2, 2, site_investment(site, inp), inp)
        parts = sum(v for k, v in cost.items() if k != "total")
        assert parts == pytest.approx(cost["total"])


def test_zero_tariff_means_no_tariff_cost(setup):
    inp, sites, _ = setup
    cost = landed_cost(sites["CN"], 0.0, 2, site_investment(sites["CN"], inp), inp)
    assert cost["tariff"] == 0


def test_landed_cost_is_a_straight_line_in_the_tariff(setup):
    inp, sites, _ = setup
    inv = site_investment(sites["CN"], inp)
    at = [landed_cost(sites["CN"], t, 2, inv, inp)["total"] for t in (0.0, 0.25, 0.5)]
    assert at[2] - at[1] == pytest.approx(at[1] - at[0])
    assert at[1] > at[0]


def test_usmca_mexico_skips_mpf_but_non_usmca_pays_it(setup):
    inp, sites, _ = setup
    mx = sites["MX"]
    inv = site_investment(mx, inp)
    usmca = landed_cost(mx, 0.0, 2, inv, inp)["us_entry_fees"]
    non_usmca = landed_cost(mx, 0.10, 2, inv, inp)["us_entry_fees"]
    assert usmca == pytest.approx(mx["broker_per_entry"] / inp["cartons_k_per_load"])
    assert non_usmca > usmca


# The merchandise processing fee part of the US entry fees, per 1,000 cartons
def mpf_per_k(site, cost, inp):
    loads_k = inp["cartons_k_per_load"]
    customs_value = (sum(cost[c] for c in ["board", "other_materials", "labor", "energy", "overhead",
                                           "capital_recovery", "supplier_margin"])
                     + site["origin_per_load"] / loads_k)
    hmf = inp["hmf_rate"] * customs_value
    fixed_fees = (site["us_port_per_load"] + site["broker_per_entry"]) / loads_k
    return cost["us_entry_fees"] - fixed_fees - hmf


def test_mpf_respects_minimum_and_maximum(setup):
    inp, sites, _ = setup
    cn = sites["CN"]
    loads_k = inp["cartons_k_per_load"]
    for rate, expected in [(1e-9, inp["mpf_min_usd"]), (1.0, inp["mpf_max_usd"])]:
        changed = dict(inp, mpf_rate=rate)
        cost = landed_cost(cn, 0.0, 2, site_investment(cn, changed), changed)
        assert mpf_per_k(cn, cost, changed) == pytest.approx(expected / loads_k)


def test_capital_recovery_repays_the_net_investment():
    capex, startup, salvage, rate, years = 5e6, 1e6, 0.4, 0.10, 5
    payment = capital_recovery_per_year(capex, startup, salvage, rate, years)
    pv_of_payments = sum(payment / (1 + rate) ** t for t in range(1, years + 1))
    assert pv_of_payments == pytest.approx(capex + startup - salvage * capex / (1 + rate) ** years)


def test_new_sites_have_a_worse_first_year(setup):
    inp, sites, _ = setup
    vn = sites["VN"]
    inv = site_investment(vn, inp)
    assert landed_cost(vn, 0.125, 1, inv, inp)["total"] > landed_cost(vn, 0.125, 2, inv, inp)["total"]


def test_staged_equals_china_plus_prep_cost_when_it_does_not_switch(setup):
    inp, sites, scenarios = setup
    today = next(s for s in scenarios if s["name"] == "status_quo")["tariff"]
    staged = staged_present_value(today, sites, inp)
    assert not staged["switched"]
    china = option_present_value("china", today, sites, inp)
    assert staged["pv"] == pytest.approx(china + inp["prep_cost_usd"])


def test_break_even_tariff_really_equalizes_costs(setup):
    inp, sites, scenarios = setup
    today = next(s for s in scenarios if s["name"] == "status_quo")["tariff"]

    def gap(t):
        tariffs = dict(today, CN=t)
        return option_present_value("china", tariffs, sites, inp) - option_present_value("vietnam", tariffs, sites, inp)

    t_star = solve_linear(gap)
    assert abs(gap(t_star)) < 1.0  # within one dollar on a ~$60M present value


def test_headline_numbers_today(setup):
    """Guards the numbers quoted in the README."""
    inp, sites, scenarios = setup
    today = next(s for s in scenarios if s["name"] == "status_quo")["tariff"]
    cost = {o: pv_to_unit_cost(option_present_value(o, today, sites, inp), inp) for o in OPTIONS}
    assert cost["china"] == pytest.approx(201.7, abs=0.05)
    assert cost["vietnam"] == pytest.approx(213.9, abs=0.05)
    assert cost["mexico"] == pytest.approx(238.5, abs=0.05)
    assert min(cost, key=cost.get) == "china"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_web_explorer_matches_python(setup):
    inp, sites, scenarios = setup
    script = """
    const M = require(process.argv[1] + '/docs/model.js');
    const D = require(process.argv[1] + '/docs/model-data.js');
    const out = {};
    for (const s of D.scenarios) {
      out[s.name] = {};
      for (const o of ['china', 'vietnam', 'mexico', 'staged'])
        out[s.name][o] = M.pvToUnitCost(M.optionPresentValue(o, s.tariff, D.sites, D.inputs), D.inputs);
    }
    console.log(JSON.stringify(out));
    """
    result = subprocess.run(["node", "-e", script, str(ROOT)], capture_output=True, text=True, check=True)
    js = json.loads(result.stdout)
    for s in scenarios:
        for option in OPTIONS:
            py = pv_to_unit_cost(option_present_value(option, s["tariff"], sites, inp), inp)
            assert js[s["name"]][option] == pytest.approx(py, abs=1e-6)
