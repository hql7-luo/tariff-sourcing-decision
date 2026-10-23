"""Static charts for the README (PNG). One consistent, quiet style for every figure."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

# Palette: one color per site, used the same way in every chart
SITE_COLORS = {"China": "#2a78d6", "Vietnam": "#eb6834", "Mexico": "#1baf7a"}
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
DIM = "#c9c8c1"

SOURCE_NOTE = ("Model inputs as of Oct 2026 (tariffs, freight, FX, board prices); "
               "see docs/data-sources.md. Fictional Zhejiang folding-carton maker.")


def use_style():
    for path in Path("/usr/share/fonts/opentype/inter").glob("Inter-*.otf"):
        font_manager.fontManager.addfont(str(path))
    plt.rcParams.update({
        "font.family": ["Inter", "DejaVu Sans"],
        "font.size": 10,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2,
        "xtick.color": MUTED,
        "ytick.color": INK_2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 200,
        "text.parse_math": False,
    })


def add_titles(fig, title, subtitle):
    fig.text(0.03, 0.965, title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(0.03, 0.905, subtitle, fontsize=10.5, color=INK_2, va="top")


def add_source(fig, text=SOURCE_NOTE):
    fig.text(0.03, 0.025, text, fontsize=8, color=MUTED, va="bottom")


def money(value):
    return f"${value:,.0f}"


# Figure 1: where the landed cost comes from, component by component
def plot_cost_components(breakdown, path):
    groups = [
        ("Total landed cost", ["total"]),
        ("Tariff", ["tariff"]),
        ("Paperboard", ["board"]),
        ("Ocean or truck freight, US entry fees", ["freight", "us_entry_fees"]),
        ("Labor", ["labor"]),
        ("Other materials, energy, overhead", ["other_materials", "energy", "overhead"]),
        ("New-plant investment", ["capital_recovery"]),
        ("Supplier margin (15%)", ["supplier_margin"]),
        ("Inventory carrying", ["inventory_carrying"]),
    ]
    data = breakdown[breakdown["period"] == "5-year average"].set_index("site")
    sites = ["China", "Vietnam", "Mexico"]

    fig, ax = plt.subplots(figsize=(10, 7.4))
    fig.subplots_adjust(left=0.30, right=0.94, top=0.80, bottom=0.13)

    bar_h = 0.24
    for row, (label, columns) in enumerate(groups):
        for k, site in enumerate(sites):
            value = data.loc[site, columns].sum()
            y = row + (k - 1) * (bar_h + 0.03)
            ax.barh(y, value, height=bar_h, color=SITE_COLORS[site], edgecolor=SURFACE, linewidth=0)
            weight = "bold" if row == 0 else "normal"
            ax.text(value + 2, y, money(value), va="center", fontsize=8.5, color=INK_2, fontweight=weight)

    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([g[0] for g in groups])
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=8)
    ax.axhline(0.55, color=AXIS, linewidth=0.8)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("USD per 1,000 cartons delivered to an LA-area warehouse", fontsize=9, color=MUTED)
    ax.xaxis.set_major_formatter(lambda v, _: money(v))

    handles = [Patch(color=SITE_COLORS[s], label=s) for s in sites]
    ax.legend(handles=handles, loc="lower right", frameon=False, ncol=3, fontsize=9.5,
              bbox_to_anchor=(1.0, 1.0), handlelength=1.0)

    totals = data["total"]
    add_titles(fig, "At today's tariffs, China still lands the cheapest carton",
               f"5-year average landed cost: China {money(totals['China'])}, Vietnam {money(totals['Vietnam'])}, "
               f"Mexico {money(totals['Mexico'])} per 1,000.\nChina pays the biggest tariff bill; "
               "new sites pay for a new plant, and Mexico pays more than twice as much for paperboard.")
    add_source(fig)
    fig.savefig(path)
    plt.close(fig)


# Figure 2: which site is cheapest for every pair of China / Vietnam tariff rates
def plot_decision_map(boundaries, scenarios, path):
    from .analysis import china_vietnam_boundary

    x_min, x_max, y_min, y_max = -1.5, 80, -1.5, 40
    x_mx = boundaries["china_mexico_tariff"] * 100
    y_mx = boundaries["vietnam_mexico_tariff"] * 100

    def boundary_x(y_pct):
        return china_vietnam_boundary(boundaries, y_pct / 100) * 100

    fig, ax = plt.subplots(figsize=(10, 6.4))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.15)

    ys = [y_min + (y_max - y_min) * i / 400 for i in range(401)]
    china_right = [min(boundary_x(y), x_mx) for y in ys]
    ax.fill_betweenx(ys, x_min, china_right, color=SITE_COLORS["China"], alpha=0.16, linewidth=0)
    vn_ys = [y for y in ys if y <= y_mx]
    ax.fill_betweenx(vn_ys, [boundary_x(y) for y in vn_ys], x_max, color=SITE_COLORS["Vietnam"],
                     alpha=0.18, linewidth=0)
    mx_ys = [y for y in ys if y >= y_mx]
    ax.fill_betweenx(mx_ys, x_mx, x_max, color=SITE_COLORS["Mexico"], alpha=0.18, linewidth=0)

    # Boundaries
    ax.plot([boundary_x(y_min), boundary_x(y_mx)], [y_min, y_mx], color=INK_2, linewidth=1.2)
    ax.plot([x_mx, x_mx], [y_mx, y_max], color=INK_2, linewidth=1.2)
    ax.plot([x_mx, x_max], [y_mx, y_mx], color=INK_2, linewidth=1.2)

    # Region labels
    ax.text(12, 31, "China is cheapest", fontsize=12.5, color=INK, fontweight="bold")
    ax.text(70, 5, "Vietnam is\ncheapest", fontsize=12.5, color=INK, fontweight="bold", ha="center")
    ax.text((x_mx + x_max) / 2, 35, "Mexico", fontsize=11.5, color=INK, fontweight="bold", ha="center")

    # Equal-tariff reference line
    ax.plot([0, 40], [0, 40], color=MUTED, linewidth=0.8)
    ax.text(30.5, 32.5, "equal tariffs", fontsize=8.5, color=MUTED, rotation=31)

    # Scenario markers
    labels = {"status_quo": ("Today (Oct 2026)", (-10, 8), "right"),
              "relief": ("Relief", (8, 6), "left"),
              "overcapacity": ("Overcapacity tariffs\n(right at break-even)", (-10, 6), "right")}
    for s in scenarios:
        if s["name"] not in labels:
            continue
        text, (dx, dy), align = labels[s["name"]]
        x, y = s["tariff"]["CN"] * 100, s["tariff"]["VN"] * 100
        today = s["name"] == "status_quo"
        ax.scatter(x, y, s=80 if today else 60, color=INK if today else SURFACE,
                   edgecolor=INK, linewidth=1.6, zorder=5)
        ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=9.5,
                    color=INK, fontweight="bold" if today else "normal", ha=align)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("US tariff on Chinese cartons", color=INK_2)
    ax.set_ylabel("US tariff on Vietnamese cartons", color=INK_2)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.tick_params(colors=MUTED)

    add_titles(fig, "Vietnam wins only if China's tariff runs about 35 points above Vietnam's",
               "Cheapest option over 5 years (ramp-up included), Mexico at its USMCA rate of 0%. "
               "Today the gap is 25 points.")
    add_source(fig)
    fig.savefig(path)
    plt.close(fig)


# Figure 3: the four strategies across 10,000 simulated futures
def plot_strategies(summary, recommended, path):
    order = summary.sort_values("mean").reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.9), gridspec_kw={"width_ratios": [1.6, 1]})
    fig.subplots_adjust(left=0.27, right=0.96, top=0.74, bottom=0.17, wspace=0.12)

    for i, row in order.iterrows():
        highlight = row["option"] == recommended
        color = INK if highlight else DIM
        ax1.plot([row["p10"], row["p90"]], [i, i], color=color, linewidth=2, solid_capstyle="round")
        ax1.scatter(row["mean"], i, s=60, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax1.text(row["p90"] + 2, i, f"avg {money(row['mean'])}", va="center", fontsize=8.5, color=INK_2)

        ax2.barh(i, row["regret_p90"], height=0.36, color=color)
        ax2.text(row["regret_p90"] + 1, i, f"${row['regret_p90']:.1f}", va="center", fontsize=8.5,
                 color=INK_2)

    ax1.set_yticks(range(len(order)))
    ax1.set_yticklabels(order["label"])
    for tick, option in zip(ax1.get_yticklabels(), order["option"]):
        if option == recommended:
            tick.set_fontweight("bold")
            tick.set_color(INK)
    ax1.invert_yaxis()
    ax1.tick_params(axis="y", length=0, pad=8)
    ax1.spines["left"].set_visible(False)
    ax1.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax1.set_axisbelow(True)
    ax1.set_xlim(160, 275)
    ax1.xaxis.set_major_formatter(lambda v, _: money(v))
    ax1.set_title("Landed cost per 1,000 cartons\n(dot = average, line = P10 to P90)", fontsize=9.5,
                  color=INK_2, loc="left")

    ax2.set_yticks(range(len(order)))
    ax2.set_yticklabels([])
    ax2.invert_yaxis()
    ax2.tick_params(axis="y", length=0)
    ax2.spines["left"].set_visible(False)
    ax2.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax2.set_axisbelow(True)
    ax2.set_xlim(0, 80)
    ax2.xaxis.set_major_formatter(lambda v, _: money(v))
    ax2.set_title("Cost of being wrong, bad case (P90)\nextra cost vs. the best choice in hindsight",
                  fontsize=9.5, color=INK_2, loc="left")

    add_titles(fig, "Stay in China, keep Vietnam ready: near-lowest cost, smallest cost of being wrong",
               "10,000 simulated futures: tariff scenario, freight, paperboard, yuan, productivity and "
               "plant cost all vary.")
    add_source(fig)
    fig.savefig(path)
    plt.close(fig)


# Figure 4: what moves the Vietnam-vs-China answer the most
def plot_sensitivity(sens, path):
    top = sens.head(8).iloc[::-1].reset_index(drop=True)
    base = top["base_gap"].iloc[0]

    fig, ax = plt.subplots(figsize=(10, 5.6))
    fig.subplots_adjust(left=0.36, right=0.95, top=0.78, bottom=0.15)

    ax.axvspan(-40, 0, color=SITE_COLORS["Vietnam"], alpha=0.07, linewidth=0)
    ax.axvspan(0, 40, color=SITE_COLORS["China"], alpha=0.07, linewidth=0)
    ax.axvline(0, color=INK_2, linewidth=1)
    ax.axvline(base, color=MUTED, linewidth=0.8)

    for i, row in top.iterrows():
        low, high = row["gap_at_low"], row["gap_at_high"]
        ax.plot([low, high], [i, i], color=INK_2, linewidth=7, solid_capstyle="butt", alpha=0.85)
        left_value, right_value = (low, high) if low < high else (high, low)
        left_label, right_label = ("low", "high") if low < high else ("high", "low")
        ax.text(left_value - 0.8, i, left_label, va="center", ha="right", fontsize=8, color=MUTED)
        ax.text(right_value + 0.8, i, right_label, va="center", ha="left", fontsize=8, color=MUTED)

    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top["driver"])
    ax.tick_params(axis="y", length=0, pad=8)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-25, 35)
    ax.xaxis.set_major_formatter(lambda v, _: f"+${v:.0f}" if v > 0 else f"-${-v:.0f}" if v < 0 else "$0")
    ax.set_xlabel("Vietnam minus China, USD per 1,000 cartons (5-year average)", fontsize=9, color=MUTED)
    ax.text(-24, len(top) - 0.35, "Vietnam cheaper", fontsize=9, color=INK_2, fontweight="bold")
    ax.text(34, len(top) - 0.35, "China cheaper", fontsize=9, color=INK_2, fontweight="bold", ha="right")
    ax.text(base + 0.6, -0.95, f"today: +${base:.0f}", fontsize=8.5, color=INK_2)
    ax.set_ylim(-1.2, len(top) - 0.1)

    add_titles(fig, "Tariffs and plant payback decide it; wages matter far less",
               "Each bar swings one input across its range while everything else stays at today's values.")
    add_source(fig)
    fig.savefig(path)
    plt.close(fig)
