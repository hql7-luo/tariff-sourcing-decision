# Decision memo: where to make cartons for our US customer

**To:** Management team · **From:** Haoqi Luo · **Date:** October 2026 · **Status:** Recommendation

## Recommendation

**Keep US production in China. Spend about $300K over the next 6 months to make Vietnam a ready option. Start the move only if China's tariff on cartons rises to about 48% (about 35 points above Vietnam's). Do not pursue Mexico for this product.**

## Why

1. **China is still the cheapest place to land a carton.** At today's tariffs the 5-year average landed cost is $201.7 per 1,000 cartons from China, $213.9 from a new Vietnam plant and $238.5 from Mexico. Over 5 years, moving to Vietnam now would cost the customer about $2.8M more in present value.
2. **The tariff gap does not yet pay for a new plant.** Vietnam's 25-point tariff advantage saves about $24 per 1,000. A new line ($5M equipment, $1M startup) costs about $21 per 1,000 to pay back over 5 years, and a new site adds rent and management overhead.
3. **Mexico's problem is paperboard.** Board is the largest cost item. North American board costs about $1,249/t delivered vs. $535/t in China, and Mexico's July 2026 antidumping duty (up to $0.49/kg) closes the route of importing Chinese board. Mexico only works with board near $910/t or a China tariff near 70%.
4. **The risk is on the upside of China's tariff.** The forced-labor Section 301 duty may be struck down (good for China), but the excess-capacity Section 301 case covers China, Vietnam and the paper sector and could raise China's rate further. In the overcapacity scenario Vietnam is already slightly cheaper ($228.6 vs. $230.0).
5. **A ready option is cheap insurance.** Across 10,000 simulated futures, staying in China is cheapest 78% of the time. Keeping Vietnam ready costs about 0.3% more on average but cuts the bad-case cost of being wrong from $4.4 to $2.8 per 1,000.

## Signposts to watch

| Signal | Action |
|---|---|
| Excess-capacity Section 301 determination puts China about 35+ points above Vietnam | Start the Vietnam move (lease, equipment order, customer requalification) |
| Court strikes down the forced-labor Section 301 duties | Stay in China; keep the Vietnam file current at low cost |
| Customer offers an 8-year volume commitment | Re-run: an 8-year payback cuts Vietnam's gap from about $12 to about $5 per 1,000 |
| Delivered board in Mexico falls below about $910/t (for example, duty-free Latin American supply) | Re-check Mexico |
| USMCA annual review fails | Keep Mexico off the list: non-qualifying cartons pay 10% |
| Ocean freight stays above $8,000 per container | Little effect on China vs. Vietnam (both ship by sea); it mainly helps Mexico |

## Next 90 days

1. Shortlist two industrial parks near Ho Chi Minh City; get written quotes for ready-built space and management fees.
2. Run sample orders with a local converter to measure real output per hour and scrap.
3. Ask the customer to pre-approve a Vietnam site and confirm the origin rules with a licensed customs broker (carton must be substantially transformed in Vietnam).
4. Replace the model's assumed plant numbers with our own cost data and re-run `run_analysis.py`.

## Main risks of this recommendation

- Tariffs move faster than a plant can be built; a sudden jump could leave a year of high-tariff shipments before Vietnam is running.
- Plant-level costs here are estimates; actual Vietnam productivity or overhead could be better or worse.
- Cost is not the only factor: a competitor already in Vietnam could win the customer on perceived risk.

Supporting analysis: [README](../README.md) · [Methodology](methodology.md) · [Data sources](data-sources.md) · [Interactive explorer](https://hql7-luo.github.io/tariff-sourcing-decision/)
