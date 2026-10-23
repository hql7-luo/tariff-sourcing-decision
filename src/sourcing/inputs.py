"""Load the model inputs and turn them into one USD parameter set per site."""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

SQFT_PER_M2 = 10.7639


# Read data/inputs.csv into a simple dict: {"fx_cny_per_usd": 6.6861, ...}
def load_inputs(path=DATA_DIR / "inputs.csv"):
    values = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            values[row["key"]] = float(row["value"])
    return values


# Read data/tariff_scenarios.csv into a list of scenario dicts
def load_scenarios(path=DATA_DIR / "tariff_scenarios.csv"):
    scenarios = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scenarios.append({
                "name": row["scenario"],
                "label": row["label"],
                "tariff": {
                    "CN": float(row["cn_tariff"]),
                    "VN": float(row["vn_tariff"]),
                    "MX": float(row["mx_tariff"]),
                },
                "probability": float(row["probability"]),
                "basis": row["basis"],
            })
    return scenarios


# Convert local-currency inputs into USD and group them by site.
# Every number the cost model uses comes from this one function.
def build_sites(inp):
    # Paperboard, USD per tonne
    cn_board = inp["cn_board_cny_per_t_incl_vat"] / (1 + inp["cn_vat_rate"]) / inp["fx_cny_per_usd"]
    vn_board = cn_board * (1 + inp["vn_board_import_uplift"])
    mx_board = inp["us_fbb_usd_per_t"] * (1 + inp["mx_board_delivery_uplift"])

    # Fully loaded labor, USD per hour
    cn_wage = (inp["cn_wage_cny_per_year"] * (1 + inp["cn_labor_load"])
               / inp["hours_per_year"] / inp["fx_cny_per_usd"])
    vn_wage = (inp["vn_wage_vnd_per_month"] * inp["vn_months_paid"] * (1 + inp["vn_labor_load"])
               / inp["hours_per_year"] / inp["fx_vnd_per_usd"])
    mx_wage = inp["mx_wage_usd_per_hour_loaded"]

    # Electricity, USD per kWh
    cn_power = inp["cn_power_cny_per_kwh"] / inp["fx_cny_per_usd"]
    vn_power = inp["vn_power_vnd_per_kwh"] / inp["fx_vnd_per_usd"]
    mx_power = inp["mx_power_mxn_per_kwh"] / inp["fx_mxn_per_usd"]

    # Yearly fixed cost of a new site (rent + site management), USD
    vn_fixed = inp["site_area_m2"] * inp["vn_rent_usd_per_m2_month"] * 12 + inp["vn_site_admin_usd_per_year"]
    mx_fixed = (inp["site_area_m2"] * SQFT_PER_M2 * inp["mx_rent_usd_per_sf_year"]
                + inp["mx_site_admin_usd_per_year"])

    # Ocean freight, USD per 40ft container
    cn_ocean = inp["ocean_cn_usd_per_feu"]
    vn_ocean = cn_ocean * inp["vn_ocean_premium"]

    common = {
        "board_kg_per_k": inp["board_kg_per_k"],
        "labor_hours_per_k": inp["labor_hours_per_k"],
        "energy_kwh_per_k": inp["energy_kwh_per_k"],
        "variable_overhead_per_k": inp["variable_overhead_usd_per_k"],
    }

    china = dict(common, **{
        "code": "CN", "name": "China", "is_new": False, "mode": "ocean",
        "board_usd_per_t": cn_board, "other_materials_per_k": inp["cn_other_materials_usd_per_k"],
        "wage_usd_per_hr": cn_wage, "productivity": 1.0, "productivity_ramp": 1.0,
        "scrap": inp["cn_scrap"], "scrap_ramp": inp["cn_scrap"],
        "power_usd_per_kwh": cn_power,
        "fixed_usd_per_k": inp["cn_fixed_usd_per_k"], "fixed_usd_per_year": 0.0,
        "freight_per_load": cn_ocean, "origin_per_load": inp["cn_origin_usd_per_load"],
        "us_port_per_load": inp["us_port_drayage_usd_per_load"],
        "broker_per_entry": inp["broker_ocean_usd_per_entry"],
        "lead_days": inp["cn_lead_days"], "safety_days": inp["cn_safety_days"],
    })

    vietnam = dict(common, **{
        "code": "VN", "name": "Vietnam", "is_new": True, "mode": "ocean",
        "board_usd_per_t": vn_board, "other_materials_per_k": inp["vn_other_materials_usd_per_k"],
        "wage_usd_per_hr": vn_wage, "productivity": inp["vn_productivity"],
        "productivity_ramp": inp["vn_productivity_ramp"],
        "scrap": inp["vn_scrap"], "scrap_ramp": inp["vn_scrap_ramp"],
        "power_usd_per_kwh": vn_power,
        "fixed_usd_per_k": 0.0, "fixed_usd_per_year": vn_fixed,
        "freight_per_load": vn_ocean, "origin_per_load": inp["vn_origin_usd_per_load"],
        "us_port_per_load": inp["us_port_drayage_usd_per_load"],
        "broker_per_entry": inp["broker_ocean_usd_per_entry"],
        "lead_days": inp["vn_lead_days"], "safety_days": inp["vn_safety_days"],
    })

    mexico = dict(common, **{
        "code": "MX", "name": "Mexico", "is_new": True, "mode": "truck",
        "board_usd_per_t": mx_board, "other_materials_per_k": inp["mx_other_materials_usd_per_k"],
        "wage_usd_per_hr": mx_wage, "productivity": inp["mx_productivity"],
        "productivity_ramp": inp["mx_productivity_ramp"],
        "scrap": inp["mx_scrap"], "scrap_ramp": inp["mx_scrap_ramp"],
        "power_usd_per_kwh": mx_power,
        "fixed_usd_per_k": 0.0, "fixed_usd_per_year": mx_fixed,
        "freight_per_load": inp["mx_truck_usd_per_load"], "origin_per_load": 0.0,
        "us_port_per_load": 0.0,
        "broker_per_entry": inp["broker_mx_usd_per_entry"],
        "lead_days": inp["mx_lead_days"], "safety_days": inp["mx_safety_days"],
    })

    return {"CN": china, "VN": vietnam, "MX": mexico}
