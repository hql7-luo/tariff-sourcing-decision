# Data sources

Every model input is in [`data/inputs.csv`](../data/inputs.csv) (marked **sourced** or **assumption**) and [`data/tariff_scenarios.csv`](../data/tariff_scenarios.csv). This page lists the public sources behind the sourced values. All were checked in October 2026; tariffs and freight change quickly, so re-check before reusing.

## US tariffs on printed folding cartons (HTS 4819.20)

| Fact used | Source |
|---|---|
| MFN rate on 4819.20 is free; Chinese cartons carry the Section 301 List 3 duty of 25% (heading 9903.88.03) | CBP ruling N317261 via [TariffLens](https://www.tarifflens.ai/rulings/N317261) |
| Chinese 4819.20 also carries the 12.5% forced-labor Section 301 duty (9903.05.31); combined 37.5% | [Wove tariff lookup, HTS 4819.20 from China](https://tariffs.wove.com/us/tariff/4819.20.00/cereal-folding-box/from/CN) |
| Forced-labor Section 301 tariffs on 60 economies from July 24, 2026: China and Vietnam 12.5%, Mexico 10%; USMCA-qualifying goods exempt | [GHY International](https://www.ghy.com/trade-compliance/ustr-section-301-forced-labor-60-economies/), [Orrick](https://www.orrick.com/en/Insights/2026/07/US-Imposes-Far-Reaching-Section-301-Tariffs) |
| The new duty stacks on top of existing China Section 301 duties | [TariffClassify, citing CBP CSMS #69326983](https://tariffclassify.ai/blog/section-301-forced-labor-tariffs-in-effect-july-2026) |
| Mexico keeps USMCA preference; the 10% applies only to non-qualifying goods | [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/07/mexico-mantiene-acceso-preferencial-bajo-el-tmec) |
| US declined to renew USMCA "in its current form" at the July 1, 2026 joint review; annual reviews follow | [Legis1](https://legis1.com/news/us-mexico-trade-deficit-1-now-top-partner-amid) |
| Excess-capacity Section 301 investigations of 16 economies (incl. China, Vietnam, Mexico; paper named as a sector) | [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/03/ustr-launches-awaited-section-301-investigations) |
| IEEPA tariffs ruled unlawful Feb 20, 2026; Section 122 tariff expired July 24, 2026 | [Penn Wharton Budget Model](https://budgetmodel.wharton.upenn.edu/p/2026-10-14-effective-tariff-rates-and-revenues-updated-october-14-2026/) |
| US–China nonsensitive product lists (Oct 2026): the examples for goods entering the US are fireworks, tableware, toys and similar; packaging is not among them, so no cut is assumed | [AgriNews / AP](https://www.agrinews-pubs.com/business/2026/10/11/us-and-china-release-60-billion-nonsensitive-product-lists-for-tariff-cuts-after-trump-xi-meeting/) |

## Paperboard

| Fact used | Source |
|---|---|
| China white cardboard benchmark ¥4,040/t (Oct 8, 2026); mills announced +¥200/t from Oct 1 | [21st Century Business Herald](https://m.21jingji.com/article/20261010/herald/42326405bd0aaa56fcb53402cdb13620.html) |
| US folding boxboard benchmark $1,178/t (July 2026) | [OPN platform, PackIndex](https://opnplatform.com/price/fbb) |
| Mexico definitive antidumping duty on Chinese coated board (cartoncillo), $0.2837 to $0.4854/kg, effective July 9, 2026 | [IDC Online](https://idconline.mx/comercio-exterior/2026/07/09/fijan-cuotas-a-importacion-de-cartoncillo-y-policarbonato), [UnoTV](https://www.unotv.com/negocios/economia-impone-cuotas-compensatorias-al-cartoncillo-importado-de-china/) |

## Freight, customs fees and lead times

| Fact used | Source |
|---|---|
| Shanghai to Los Angeles $7,884 per 40ft (Oct 15, 2026) | [DCN, Drewry WCI](https://www.thedcn.com.au/news/world-container-index-15-october-2026) |
| Shanghai to Los Angeles $3,132 per 40ft (Jan 8, 2026), low end of the simulation range | [DCN, Drewry WCI](https://www.thedcn.com.au/news/world-container-index-8-january-2026) |
| Ho Chi Minh City to Los Angeles transit 27 to 36 days | [Freightos](https://www.freightos.com/routes/route/vn-hochiminhcity/us-losangeles-ca) |
| LA port to Ontario, CA drayage about $650 base plus fuel (bids Jul to Oct 2026) | [Gateway Lines](https://gatewaylines.com/los-angeles-drayage-rates) |
| Tijuana to Los Angeles truck transit 3 to 5 days | [Cargado](https://cargado.com/lanes/tijuana-bcn-to-los-angeles-ca) |
| Merchandise processing fee 0.3464%, min $34.58, max $670.86 (from Oct 1, 2026) | [C.H. Robinson advisory](https://www.chrobinson.com/en-sg/resources/insights-and-advisories/client-advisories/2026q3/09-18-26-client-advisory-us-customs-and-border-protection-trade-and-customs-update/) |
| Harbor maintenance fee 0.125% on ocean entries | 19 CFR 24.24 |

## Exchange rates, wages, energy, rent

| Fact used | Source |
|---|---|
| ¥6.6861 and MX$18.5026 per USD (Oct 16, 2026) | [Federal Reserve H.10](https://www.federalreserve.gov/Releases/H10/Current/) |
| ₫25,639 per USD central rate (Oct 20, 2026) | [State Bank of Vietnam, via Thi truong Tai chinh Tien te](https://thitruongtaichinhtiente.vn/ngay-20-10-ty-gia-trung-tam-tang-6-dong-86422.html) |
| China 2025 average wage, private manufacturing units ¥76,055 | [National Bureau of Statistics](https://www.stats.gov.cn/xxgk/sjfb/zxfb2020/202605/t20260515_1963707.html) |
| Vietnam Q1 2026 salaried workers average ₫10.0 million/month | [Tuoi Tre, citing the National Statistics Office](https://news.tuoitre.vn/vietnam-q1-incomes-rise-85-y-y-as-labor-market-stays-stable-statistics-office-103260405084546016.htm) |
| Mexico border-zone loaded labor cost about $5.50/hour | [Cosmo Sourcing](https://www.cosmosourcing.com/blog/mexico-manufacturing-wages-labor-costs) |
| Business electricity: China ¥0.796, Vietnam ₫2,088.9, Mexico MX$3.974 per kWh (June 2025) | GlobalPetrolPrices: [China](https://www.globalpetrolprices.com/China/), [Vietnam](https://www.globalpetrolprices.com/Vietnam/), [Mexico](https://www.globalpetrolprices.com/Mexico/) |
| Ready-built factory rent near Ho Chi Minh City, $4.5 to $6.0 per m² per month (2026) | [United Consulting](https://unitedconsulting.odoo.com/blog/united-consulting-blog-1/vietnam-factory-setup-costs-for-industrial-parks-near-hcmc-74) |
| Tijuana industrial asking rent $9.42 per sq ft per year (1Q26) | [Newmark](https://nmrk.imgix.net/uploads/fields/pdf-market-reports/NMRK-2026-1Q-TIJ-INDUSTRIAL_SF_EN.pdf) |

## What is assumed rather than sourced

Plant-level numbers: carton weight, labor hours per 1,000 cartons, productivity and scrap at new sites, other materials, overhead, site management cost, equipment and startup cost, supplier margin, safety stock days, origin charges, the Mexico truck rate and broker fees. Scenario probabilities are judgment calls. All are flagged `assumption` in `data/inputs.csv`; the sensitivity chart shows which of them could change the answer.
