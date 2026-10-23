# Methodology

## 1. The question

A fictional printed folding-carton maker in Taizhou, Zhejiang supplies one US customer with 60 million retail cartons a year (mid-size box, about 88 kg of paperboard per 1,000 cartons). The customer compares suppliers on **landed cost**: what it pays per carton delivered to its warehouse in the Los Angeles area, including tariffs. If a competitor can land the carton cheaper, the business is at risk. So the maker asks: where should US production be in the next five years?

## 2. Landed cost per 1,000 cartons

Code: [`src/sourcing/model.py`](../src/sourcing/model.py), function `landed_cost`.

**Factory cost** (grossed up for scrap, so it is the cost per *good* carton):

- Paperboard = kg per 1,000 × board price per tonne
- Other materials (ink, coating, glue, foil, shipping cases)
- Labor = hours per 1,000 ÷ productivity × loaded wage
- Energy = kWh per 1,000 × electricity price
- Overhead = variable overhead + site fixed cost ÷ volume
- New-plant payback = yearly capital recovery ÷ volume (new sites only)

**Supplier price (customs value)** = factory cost × (1 + 15% margin) + origin charges (trucking to port, export docs).

**Delivered cost** adds:

- Freight: ocean per 40ft container (China, Vietnam) or truck per trailer (Mexico), divided by 200,000 cartons per load
- US entry fees: port drayage, broker, merchandise processing fee (0.3464%, with a floor and a cap per entry; waived for USMCA-qualifying goods), harbor maintenance fee (0.125%, ocean only)
- Tariff = tariff rate × customs value
- Inventory carrying = 20% a year × value × (door-to-door days + safety stock days) ÷ 365

Landed cost is a straight line in each tariff rate. That is why break-even points can be solved exactly (`solve_linear` in `analysis.py`) and why the decision map has straight boundaries.

### Converting inputs to US dollars

`build_sites` in [`inputs.py`](../src/sourcing/inputs.py) does every conversion in one place:

| Site | Board | Loaded wage | Notes |
|---|---|---|---|
| China | ¥4,040/t ÷ 1.13 VAT ÷ 6.6861 = **$535/t** | ¥76,055 × 1.30 ÷ 2,300 h ÷ 6.6861 = **$6.43/h** | Existing plant: no new investment, $10 per 1,000 fixed overhead |
| Vietnam | China board + 12% import cost = **$599/t** | ₫10.0M × 13 months × 1.235 ÷ 2,300 h ÷ 25,639 = **$2.72/h** | Imports board from China (no Vietnamese trade remedy found) |
| Mexico | US benchmark $1,178/t + 6% delivery = **$1,249/t** | **$5.50/h** loaded | Chinese board faces Mexico's antidumping duty (up to $0.49/kg), so it is not a cheaper route |

China's wage is higher than Mexico's in dollars, and Vietnam's is far lower, but labor is only 3% to 6% of landed cost for this product. Paperboard, tariffs and new-plant costs dominate.

## 3. Strategies and the five-year view

Code: `option_present_value`, `staged_present_value`.

| Strategy | What happens |
|---|---|
| Stay in China | China serves all volume for 5 years |
| Move to Vietnam now | New Vietnam plant serves all volume from year 1 (ramp-up year: 60% productivity, 10% scrap) |
| Move to Mexico now | New Tijuana plant, same logic (65% productivity, 9% scrap in year 1) |
| Stay in China, keep Vietnam ready | Pay $300K now for site shortlist, entity setup, sample runs and customer pre-approval. Serve from China in year 1. From year 2, run whichever of China or Vietnam is cheaper once the tariff path is known |

Each strategy's yearly spend is discounted at 10% and summed over 5 years. Results are shown as the **average landed cost per 1,000 cartons** with the same present value, so all numbers are comparable.

**New-plant investment** ($5M equipment + $1M startup, 40% equipment resale value after 5 years) is turned into an equal yearly charge with a capital recovery factor, like a loan payment. A plant opened in year 2 is charged the same yearly amount, because it keeps running after the horizon.

## 4. Tariff scenarios

From [`data/tariff_scenarios.csv`](../data/tariff_scenarios.csv). Probabilities are judgment calls, shown so they can be challenged.

| Scenario | China | Vietnam | Mexico | Probability | Story |
|---|---:|---:|---:|---:|---|
| Status quo (Oct 2026) | 37.5% | 12.5% | 0% | 40% | Today's stack holds |
| Relief | 25% | 0% | 0% | 20% | Forced-labor Section 301 tariffs struck down in court or dropped |
| Overcapacity tariffs | 62.5% | 22.5% | 0% | 30% | Excess-capacity Section 301 adds 25 points on China and 10 on Vietnam; USMCA goods stay exempt |
| USMCA friction | 37.5% | 12.5% | 10% | 10% | Mexican cartons lose USMCA preference |

## 5. Simulation

Code: [`src/sourcing/simulate.py`](../src/sourcing/simulate.py). 10,000 runs, fixed seed. Each run draws a tariff scenario by its probability and eight inputs from triangular distributions (low, most likely, high):

| Input | Range | Why |
|---|---|---|
| Ocean freight, Shanghai–LA | $3,132 / $5,500 / $8,500 | Jan 2026 level to above today's $7,884 spike |
| China board price | ±15% | One year of price swings |
| US board price | $940 / $1,178 / $1,300 | Cheaper Latin American supply to further increases |
| Yuan per USD | 6.30 / 6.69 / 7.10 | Stronger yuan makes China dearer in dollars |
| Vietnam productivity | 70% / 80% / 90% of China | Speed of learning at a new site |
| Mexico productivity | 75% / 85% / 95% | Same |
| Mexico loaded wage | $5.00 / $5.50 / $6.60 | 40-hour week reform could add up to 20% |
| Equipment cost | $3.0M / $5.0M / $6.5M | Used equipment to overruns |

Because the freight range centers below today's spike, simulated cost levels are lower than the today-only figures. The comparison between strategies is what matters.

**Cost of being wrong (regret).** In each run, a strategy's regret is its cost minus the cost of the best strategy for that run, judged with hindsight. The chart shows the 90th percentile: how much you overpay in a bad case. "Keep Vietnam ready" is never the cheapest in a single run (it pays the preparation cost, and moving at once is cheaper whenever Vietnam wins outright), but it has the smallest bad-case regret.

## 6. Sensitivity and thresholds

Code: `sensitivity`, `thresholds`, `decision_boundaries` in [`analysis.py`](../src/sourcing/analysis.py).

- **Break-even China tariff vs. Vietnam:** 48.3% with Vietnam at 12.5% (today 37.5%). Across Vietnam rates of 0% to 30% the break-even gap is 32 to 41 points, about 35 on average.
- **Break-even China tariff vs. Mexico:** 70.0% (Mexico at 0%).
- **Mexico board price that would match China today:** about $908/t delivered (vs. $1,249).
- **Tornado chart:** each input is moved across its range alone. Tariffs and the payback period swing the Vietnam-minus-China gap by $21 to $42 per 1,000, plant cost by $15, and wages, freight and board prices by under $8.

## 7. Checks

[`tests/test_model.py`](../tests/test_model.py) checks that components add up, tariffs enter linearly, fee floors and caps work, USMCA goods skip the processing fee, the capital charge repays the investment, break-even points really equalize costs, the README headline numbers hold, and the JavaScript explorer returns the same numbers as Python.

## 8. Limits

- Plant-level inputs are assumptions for a fictional company.
- One product and one customer location; a Midwest or Texas customer would favor Mexico more.
- Costs are in constant 2026 dollars; no wage or price escalation inside the horizon.
- Tariff scenarios hold for all five years; the staged strategy assumes the path is clear by year 2.
- Not modeled: customer service value of speed, quality and requalification risk, transshipment audits, tax incentives (Vietnam investment incentives, Mexico IMMEX), currency hedging.
