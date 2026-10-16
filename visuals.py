"""Data-derived publishing graphic and a first-step-focused project roadmap."""

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/linkedin-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

ROOT = Path(__file__).resolve().parent
BLUE, RED, YELLOW, INK, PAPER = "#2456E8", "#E7433D", "#F5D547", "#142B66", "#F2F5FF"
MUTED, LINE = "#53658D", "#DCE4F8"
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path"})


def euro(value):
    return f"{'−' if value < 0 else ''}€{abs(value) / 1000:,.0f}k"


def text(fig, x, y, value, size=12, color=INK, weight="normal", **kwargs):
    return fig.text(x, y, value, fontsize=size, color=color, weight=weight, **kwargs)


def box(fig, x, y, width, height, color, edge=None):
    fig.add_artist(Rectangle((x, y), width, height, transform=fig.transFigure, facecolor=color,
                             edgecolor=edge or color, linewidth=.8, zorder=0))


def brand(fig, label):
    for i, (height, color) in enumerate(zip((.008, .015, .022), (BLUE, RED, YELLOW))):
        box(fig, .055 + .009*i, .95, .006, height, color)
    text(fig, .098, .951, "ANALYSIS NOTES", 11, BLUE, "bold")
    text(fig, .945, .951, label, 10, BLUE, "bold", ha="right")
    box(fig, .055, .928, .89, .002, BLUE)


def save(fig, name):
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(output / f"{name}.{ext}", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def roadmap(report):
    fig = plt.figure(figsize=(12, 9), facecolor=PAPER)
    brand(fig, "002 / PROJECT ROADMAP")
    text(fig, .055, .882, "Retail Margin Leak\n& Action Engine", 30, BLUE, "bold", va="top", linespacing=1.05)
    text(fig, .055, .742, "START WITH THE BUSINESS QUESTION", 10, RED, "bold")
    box(fig, .055, .412, .425, .297, BLUE)
    text(fig, .079, .668, "01 / DEFINE THE PROBLEM", 12, YELLOW, "bold")
    text(fig, .079, .610, "Sales are growing.\nWhy is profit falling?", 23, "white", "bold", va="top", linespacing=1.2)
    text(fig, .079, .484, "Locate the loss. Explain the drivers.\nPrioritize a commercial test.", 13, "white", va="top", linespacing=1.5)
    steps = [
        ("02", "Scope + hypotheses", "Discounts / joint mix / supplier cost"),
        ("03", "Build the retail environment", "Six tables + separately held planted labels"),
        ("04", "Define the KPI contract", "Net sales / product COGS / gross profit"),
        ("05", "Reconcile and diagnose", "Exact bridge + location drill-down"),
        ("06", "Prioritize actions", "Rules + fixed-volume scenario assumptions"),
        ("07", "Deliver and verify", "Dashboard / reproducible code / evaluation"),
    ]
    for index, (number, title, subtitle) in enumerate(steps):
        y = .806 - index * .116
        box(fig, .563, y - .055, .382, .091, "white", LINE)
        fig.add_artist(Circle((.543, y - .009), .019, transform=fig.transFigure, facecolor=YELLOW, edgecolor=PAPER, linewidth=3, zorder=2))
        text(fig, .543, y - .009, number, 10, INK, "bold", ha="center", va="center")
        text(fig, .588, y + .004, title, 14, INK, "bold")
        text(fig, .588, y - .027, subtitle, 10, MUTED)
        if index < 5:
            fig.add_artist(FancyArrowPatch((.543, y - .030), (.543, y - .104), transform=fig.transFigure,
                                          arrowstyle="-|>", mutation_scale=11, color=BLUE, lw=1.4, zorder=1))
    text(fig, .055, .357, "CONTROLLED SYNTHETIC ENVIRONMENT", 10, BLUE, "bold")
    for i, (number, label) in enumerate((("500", "SKUs"), (f"{report['audit']['row_counts']['fact_sales']/1000:g}k", "sales lines"), ("12", "months"))):
        x = .055 + i*.145
        text(fig, x, .299, number, 25, INK, "bold")
        text(fig, x, .270, label, 11, MUTED)
    text(fig, .055, .216, "SCALE / PROTECT / MODIFY\nINVESTIGATE / STOP", 13, INK, "bold", linespacing=1.4)
    text(fig, .055, .125, "Decision support for pricing, category\nand commercial teams.", 12, MUTED, linespacing=1.4)
    text(fig, .055, .045, "Accounting attribution + scenario analysis. No causal uplift, demand forecast or live deployment.", 10, MUTED)
    save(fig, "roadmap")


def overview(report):
    company = report["slices"]["All|All|All"]
    before, after = company["periods"]
    bridge = company["bridge"]
    fig = plt.figure(figsize=(9.6, 12), facecolor=PAPER)
    brand(fig, "002 / RETAIL MARGIN")
    revenue_word = "up" if company["revenue_change"] >= 0 else "down"
    gp_word = "up" if company["gp_change"] >= 0 else "down"
    text(fig, .055, .893, f"Revenue {revenue_word} {abs(company['revenue_change']):.1%}.\nGross profit {gp_word} {abs(company['gp_change']):.1%}.", 30, BLUE, "bold", va="top", linespacing=1.15)
    text(fig, .055, .775, "Which accounting drivers explain the difference?", 14, MUTED)
    for i, (value, label) in enumerate(((f"{before['margin']:.1%} → {after['margin']:.1%}", "GROSS MARGIN"),
                                      (euro(after["gp"] - before["gp"]), "NET GP CHANGE"),
                                      ("H1 → H2", "2025 / SYNTHETIC"))):
        x = .055 + i * .305
        text(fig, x, .727, label, 10, MUTED, "bold")
        text(fig, x, .691, value, 20, INK, "bold")
    box(fig, .055, .376, .89, .277, "white", LINE)
    text(fig, .078, .626, "01 / EXACT GROSS-PROFIT BRIDGE", 11, BLUE, "bold")
    ax = fig.add_axes([.108, .444, .79, .152], facecolor="white")
    effects = list(bridge["effects"].values())
    running = bridge["baseline_gp"]
    values = [(0, running)]
    for amount in effects:
        values.append((running, running + amount))
        running += amount
    values.append((0, bridge["current_gp"]))
    maximum = max(max(a, b) for a, b in values)
    ax.set_ylim(0, maximum * 1.18)
    ax.set_xlim(-.6, 6.6)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.set_yticks([0, 2000000, 4000000], ["€0", "€2m", "€4m"])
    ax.tick_params(length=0, colors=MUTED, labelsize=9)
    ax.set_xticks(range(7), ["H1 GP", "Volume", "Joint\nmix", "List\nprice", "Discount", "Cost", "H2 GP"])
    for index, (start, end) in enumerate(values):
        total = index in (0, 6)
        amount = end if total else end-start
        color = YELLOW if index == 6 else BLUE if total or amount >= 0 else RED
        ax.bar(index, max(abs(end-start), maximum*.001), bottom=min(start,end), width=.64, color=color, zorder=3)
        label = euro(amount) if total else ("+" if amount >= 0 else "") + euro(amount)
        ax.text(index, max(start,end) + maximum*.035, label, fontsize=9.5, color=INK, weight="bold", ha="center")
        if index < 6:
            ax.plot([index+.32,index+.68], [end,end], color="#ACBADD", lw=.8, ls="--")
    text(fig, .078, .393, "Joint mix = SKU × region × channel. Effects reconcile to the GP change.", 9.5, MUTED)
    text(fig, .055, .344, "02 / LOCATE THE CHANGE", 11, BLUE, "bold")
    categories = [(category, report["slices"][f"{category}|All|All"]["bridge"]) for category in report["categories"]]
    categories.sort(key=lambda item: item[1]["current_gp"]-item[1]["baseline_gp"])
    for i, (category, local) in enumerate(categories):
        y = .306 - i*.031
        delta = local["current_gp"]-local["baseline_gp"]
        text(fig, .055, y, category, 12)
        text(fig, .47, y, ("+" if delta >= 0 else "")+euro(delta), 12, RED if delta < 0 else BLUE, "bold", ha="right")
    box(fig, .535, .166, .41, .164, YELLOW)
    text(fig, .557, .301, "03 / PRIORITIZE A TEST", 10, INK, "bold")
    text(fig, .557, .263, euro(report["scenario_total"]), 27, INK, "bold")
    text(fig, .557, .235, "Fixed-volume action scenarios", 11, INK, "bold")
    text(fig, .557, .206, "Demand response excluded.\nNot a recovery forecast.", 10, INK, linespacing=1.4)
    box(fig, .055, .116, .89, .002, BLUE)
    text(fig, .055, .089, f"SYNTHETIC DATA · 500 SKUs · {report['audit']['row_counts']['fact_sales']:,} sales lines · EUR", 10.5, INK, "bold")
    text(fig, .055, .066, "Accounting attribution is not causal identification. Stock and customer signals are separate diagnostics.", 9, MUTED)
    text(fig, .055, .043, "Code, KPI definitions, exact reconciliation and action assumptions are in the companion project.", 9, MUTED)
    save(fig, "analysis")


def write_post(report):
    company = report["slices"]["All|All|All"]
    solution = json.loads((ROOT / "outputs/discount-solution.json").read_text())
    post = (
        "Sales are growing. Why is profit falling?\n\n"
        f"I built a retail analytics project using 12 months of synthetic data covering 500 products and {report['audit']['row_counts']['fact_sales']:,} sales lines.\n\n"
        f"Revenue grew {company['revenue_change']:.1%}, while gross profit fell {abs(company['gp_change']):.1%}.\n\n"
        "Using SQL and Python, I separated the effects of volume, sales mix, prices, discounts and costs. Discounting was the biggest negative driver.\n\n"
        "The proposed fix: reduce discounts by up to six percentage points on flagged offers—for example, from 20% to 14%.\n\n"
        f"At unchanged sales volume, this added {euro(solution['modeled_gain_eur'])} in modeled gross profit, enough to close the {euro(solution['profit_gap_eur'])} gap.\n\n"
        "This is a scenario result. Customers may buy less when discounts shrink, so the next step would be a controlled test measuring both units sold and gross profit.\n"
    )
    (ROOT / "post.en.md").write_text(post)


def render():
    report = json.loads((ROOT / "outputs/report.json").read_text())
    overview(report)
    write_post(report)
    print("Rendered analysis.png, analysis.svg and the English post.")


if __name__ == "__main__":
    render()

