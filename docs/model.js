// Landed cost model for the web explorer.
// A line-by-line port of src/sourcing/model.py; tests/test_explorer.py checks both give the same numbers.

(function (root) {
  const COMPONENTS = [
    "board", "other_materials", "labor", "energy", "overhead", "capital_recovery",
    "supplier_margin", "freight", "us_entry_fees", "tariff", "inventory_carrying",
  ];

  // One-time investment turned into an equal yearly charge, after equipment resale value
  function capitalRecoveryPerYear(capex, startup, salvageShare, rate, years) {
    const netPresentCost = capex + startup - salvageShare * capex / Math.pow(1 + rate, years);
    const factor = rate / (1 - Math.pow(1 + rate, -years));
    return netPresentCost * factor;
  }

  function siteInvestment(site, inp) {
    if (!site.is_new) return { capital_per_year: 0, fixed_per_year: 0 };
    const capital = capitalRecoveryPerYear(inp.capex_usd, inp.startup_usd, inp.salvage_share,
      inp.discount_rate, inp.horizon_years);
    return { capital_per_year: capital, fixed_per_year: site.fixed_usd_per_year };
  }

  // Landed cost per 1,000 good cartons; siteYear 1 = ramp-up year of a new site
  function landedCost(site, tariff, siteYear, investment, inp) {
    const volumeK = inp.annual_volume_k;
    const rampUp = site.is_new && siteYear === 1;
    const productivity = rampUp ? site.productivity_ramp : site.productivity;
    const scrap = rampUp ? site.scrap_ramp : site.scrap;
    const scrapFactor = 1 / (1 - scrap);

    const c = {};
    c.board = site.board_kg_per_k * site.board_usd_per_t / 1000 * scrapFactor;
    c.other_materials = site.other_materials_per_k * scrapFactor;
    c.labor = site.labor_hours_per_k / productivity * site.wage_usd_per_hr * scrapFactor;
    c.energy = site.energy_kwh_per_k * site.power_usd_per_kwh * scrapFactor;
    c.overhead = site.variable_overhead_per_k * scrapFactor + site.fixed_usd_per_k
      + investment.fixed_per_year / volumeK;
    c.capital_recovery = investment.capital_per_year / volumeK;
    const production = c.board + c.other_materials + c.labor + c.energy + c.overhead + c.capital_recovery;

    const loadsK = inp.cartons_k_per_load;
    c.supplier_margin = production * inp.margin_on_cost;
    const origin = site.origin_per_load / loadsK;
    const customsValue = production + c.supplier_margin + origin;

    c.freight = origin + site.freight_per_load / loadsK;

    const usmca = site.code === "MX" && tariff === 0;
    let mpf = 0;
    if (!usmca) {
      const valuePerEntry = customsValue * loadsK;
      mpf = Math.min(Math.max(inp.mpf_rate * valuePerEntry, inp.mpf_min_usd), inp.mpf_max_usd) / loadsK;
    }
    const hmf = site.mode === "ocean" ? inp.hmf_rate * customsValue : 0;
    c.us_entry_fees = (site.us_port_per_load + site.broker_per_entry) / loadsK + mpf + hmf;

    c.tariff = tariff * customsValue;

    const beforeCarrying = COMPONENTS.slice(0, 10).reduce((sum, k) => sum + c[k], 0);
    const days = site.lead_days + site.safety_days;
    c.inventory_carrying = inp.holding_rate * beforeCarrying * days / 365;

    c.total = COMPONENTS.reduce((sum, k) => sum + c[k], 0);
    return c;
  }

  function sitePresentValue(site, tariff, inp, firstYear) {
    firstYear = firstYear || 1;
    const investment = siteInvestment(site, inp);
    let pv = 0;
    for (let year = firstYear; year <= inp.horizon_years; year++) {
      const unit = landedCost(site, tariff, year - firstYear + 1, investment, inp).total;
      pv += unit * inp.annual_volume_k / Math.pow(1 + inp.discount_rate, year);
    }
    return pv;
  }

  function stagedPresentValue(tariffs, sites, inp) {
    const chinaInv = siteInvestment(sites.CN, inp);
    const yearOne = landedCost(sites.CN, tariffs.CN, 1, chinaInv, inp).total * inp.annual_volume_k;
    const stay = sitePresentValue(sites.CN, tariffs.CN, inp, 2);
    const sw = sitePresentValue(sites.VN, tariffs.VN, inp, 2);
    return { pv: inp.prep_cost_usd + yearOne / (1 + inp.discount_rate) + Math.min(stay, sw), switched: sw < stay };
  }

  function optionPresentValue(option, tariffs, sites, inp) {
    if (option === "china") return sitePresentValue(sites.CN, tariffs.CN, inp);
    if (option === "vietnam") return sitePresentValue(sites.VN, tariffs.VN, inp);
    if (option === "mexico") return sitePresentValue(sites.MX, tariffs.MX, inp);
    if (option === "staged") return stagedPresentValue(tariffs, sites, inp).pv;
    throw new Error("Unknown option " + option);
  }

  function pvToUnitCost(pv, inp) {
    let annuity = 0;
    for (let year = 1; year <= inp.horizon_years; year++) annuity += 1 / Math.pow(1 + inp.discount_rate, year);
    return pv / (annuity * inp.annual_volume_k);
  }

  // 5-year average cost per component (present-value weighted), matching the README chart
  function averageBreakdown(site, tariff, inp) {
    const investment = siteInvestment(site, inp);
    const out = {};
    let weightSum = 0;
    COMPONENTS.concat(["total"]).forEach((k) => { out[k] = 0; });
    for (let year = 1; year <= inp.horizon_years; year++) {
      const w = 1 / Math.pow(1 + inp.discount_rate, year);
      const c = landedCost(site, tariff, year, investment, inp);
      weightSum += w;
      COMPONENTS.concat(["total"]).forEach((k) => { out[k] += w * c[k]; });
    }
    COMPONENTS.concat(["total"]).forEach((k) => { out[k] /= weightSum; });
    return out;
  }

  const api = { COMPONENTS, landedCost, siteInvestment, optionPresentValue, stagedPresentValue,
    pvToUnitCost, averageBreakdown };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.SourcingModel = api;
})(this);
