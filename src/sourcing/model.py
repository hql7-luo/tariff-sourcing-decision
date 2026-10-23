"""Landed cost model: what one US customer pays per 1,000 cartons delivered to its LA-area warehouse."""

# The four strategies the analysis compares
OPTIONS = {
    "china":   "Stay in China",
    "vietnam": "Move to Vietnam now",
    "mexico":  "Move to Mexico now",
    "staged":  "Stay in China, keep Vietnam ready",
}

# Order of cost components (used for tables and stacked charts)
COMPONENTS = [
    "board", "other_materials", "labor", "energy", "overhead", "capital_recovery",
    "supplier_margin", "freight", "us_entry_fees", "tariff", "inventory_carrying",
]


# Turn a one-time investment into an equal yearly charge, like a loan payment,
# after crediting the equipment resale value at the end.
def capital_recovery_per_year(capex, startup, salvage_share, rate, years):
    net_present_cost = capex + startup - salvage_share * capex / (1 + rate) ** years
    capital_recovery_factor = rate / (1 - (1 + rate) ** -years)
    return net_present_cost * capital_recovery_factor


# Yearly charges that come with running a site: new sites carry rent, site
# management and the recovery of the equipment investment over the horizon.
def site_investment(site, inp):
    if not site["is_new"]:
        return {"capital_per_year": 0.0, "fixed_per_year": 0.0}
    years = int(inp["horizon_years"])
    capital = capital_recovery_per_year(inp["capex_usd"], inp["startup_usd"], inp["salvage_share"],
                                        inp["discount_rate"], years)
    return {"capital_per_year": capital, "fixed_per_year": site["fixed_usd_per_year"]}


# Landed cost per 1,000 good cartons for one site.
# site_year = 1 is the ramp-up year of a new site (lower output per hour, more scrap).
def landed_cost(site, tariff, site_year, investment, inp):
    volume_k = inp["annual_volume_k"]
    ramp_up = site["is_new"] and site_year == 1
    productivity = site["productivity_ramp"] if ramp_up else site["productivity"]
    scrap = site["scrap_ramp"] if ramp_up else site["scrap"]

    # 1) Production cost per 1,000 cartons, grossed up for scrap
    scrap_factor = 1 / (1 - scrap)
    cost = {}
    cost["board"] = site["board_kg_per_k"] * site["board_usd_per_t"] / 1000 * scrap_factor
    cost["other_materials"] = site["other_materials_per_k"] * scrap_factor
    cost["labor"] = site["labor_hours_per_k"] / productivity * site["wage_usd_per_hr"] * scrap_factor
    cost["energy"] = site["energy_kwh_per_k"] * site["power_usd_per_kwh"] * scrap_factor
    cost["overhead"] = (site["variable_overhead_per_k"] * scrap_factor
                        + site["fixed_usd_per_k"]
                        + investment["fixed_per_year"] / volume_k)
    cost["capital_recovery"] = investment["capital_per_year"] / volume_k
    production = sum(cost.values())

    # 2) Supplier price (the customs value): production cost + margin + origin charges
    loads_k = inp["cartons_k_per_load"]
    cost["supplier_margin"] = production * inp["margin_on_cost"]
    origin = site["origin_per_load"] / loads_k
    customs_value = production + cost["supplier_margin"] + origin

    # 3) Freight, US entry fees and tariff
    cost["freight"] = origin + site["freight_per_load"] / loads_k

    # USMCA-qualifying Mexican goods (Mexico tariff = 0) skip the merchandise
    # processing fee; the harbor maintenance fee only applies to ocean entries.
    usmca = site["code"] == "MX" and tariff == 0
    if usmca:
        mpf = 0.0
    else:
        value_per_entry = customs_value * loads_k
        mpf = min(max(inp["mpf_rate"] * value_per_entry, inp["mpf_min_usd"]), inp["mpf_max_usd"]) / loads_k
    hmf = inp["hmf_rate"] * customs_value if site["mode"] == "ocean" else 0.0
    cost["us_entry_fees"] = (site["us_port_per_load"] + site["broker_per_entry"]) / loads_k + mpf + hmf

    cost["tariff"] = tariff * customs_value

    # 4) Inventory carrying: cash tied up in transit and in safety stock
    before_carrying = sum(cost.values())
    days = site["lead_days"] + site["safety_days"]
    cost["inventory_carrying"] = inp["holding_rate"] * before_carrying * days / 365

    cost["total"] = sum(cost[c] for c in COMPONENTS)
    return cost


# Present value of the customer's yearly spend when one site serves all volume
# from calendar year `first_year` to the end of the horizon.
# A plant opened in year 2 keeps running after the horizon ends, so its yearly
# capital charge is the same as for a plant opened in year 1.
def site_present_value(site, tariff, inp, first_year=1):
    rate = inp["discount_rate"]
    horizon = int(inp["horizon_years"])
    investment = site_investment(site, inp)

    pv = 0.0
    for year in range(first_year, horizon + 1):
        site_year = year - first_year + 1
        unit = landed_cost(site, tariff, site_year, investment, inp)["total"]
        pv += unit * inp["annual_volume_k"] / (1 + rate) ** year
    return pv


# Present value (USD) of the customer's total spend over the horizon for one strategy.
# "staged": pay a small preparation cost now, stay in China in year 1, then from
# year 2 run whichever of China or Vietnam is cheaper once the tariff path is known.
def option_present_value(option, tariffs, sites, inp):
    if option == "china":
        return site_present_value(sites["CN"], tariffs["CN"], inp)
    if option == "vietnam":
        return site_present_value(sites["VN"], tariffs["VN"], inp)
    if option == "mexico":
        return site_present_value(sites["MX"], tariffs["MX"], inp)
    if option == "staged":
        return staged_present_value(tariffs, sites, inp)["pv"]
    raise ValueError(f"Unknown option: {option}")


def staged_present_value(tariffs, sites, inp):
    rate = inp["discount_rate"]
    china_inv = site_investment(sites["CN"], inp)
    year_one = landed_cost(sites["CN"], tariffs["CN"], 1, china_inv, inp)["total"] * inp["annual_volume_k"]

    stay = site_present_value(sites["CN"], tariffs["CN"], inp, first_year=2)
    switch = site_present_value(sites["VN"], tariffs["VN"], inp, first_year=2)
    pv = inp["prep_cost_usd"] + year_one / (1 + rate) + min(stay, switch)
    return {"pv": pv, "switched": switch < stay}


# Average landed cost per 1,000 cartons that has the same present value as `pv`
def pv_to_unit_cost(pv, inp):
    rate = inp["discount_rate"]
    horizon = int(inp["horizon_years"])
    annuity = sum(1 / (1 + rate) ** year for year in range(1, horizon + 1))
    return pv / (annuity * inp["annual_volume_k"])


# Landed cost is a straight line in the tariff rate, so two points give the
# value of `tariff` at which `site` costs exactly `target` per 1,000 cartons.
def tariff_to_match(site, target, inp, site_year=2):
    investment = site_investment(site, inp)
    at_zero = landed_cost(site, 0.0, site_year, investment, inp)["total"]
    at_one = landed_cost(site, 1.0, site_year, investment, inp)["total"]
    return (target - at_zero) / (at_one - at_zero)


# China tariff at which China's steady-state landed cost equals another site's
def china_break_even_tariff(other_code, other_tariff, sites, inp):
    other_site = sites[other_code]
    other = landed_cost(other_site, other_tariff, 2, site_investment(other_site, inp), inp)["total"]
    return tariff_to_match(sites["CN"], other, inp)
