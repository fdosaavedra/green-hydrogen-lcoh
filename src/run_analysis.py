"""Reproduce the base case, the sensitivity analysis and the cost-reduction scenario."""
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt

from lcoh import LCOHInputs, breakdown, lcoh, sensitivity

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": INK, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE})


def style(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color="#e5e4df", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)


base = LCOHInputs()
total = lcoh(base)
print(f"Base-case LCOH: {total:.2f} USD/kg")
for k, v in breakdown(base).items():
    print(f"  {k:<28} {v:7.3f} USD/kg  ({v / total:6.1%})")

# 1) Cost breakdown
parts = breakdown(base)
fig, ax = plt.subplots(figsize=(8, 3.4))
names = list(parts)[::-1]
vals = [parts[n] for n in names]
ax.barh(names, vals, color=BLUE, height=0.55)
for y, v in enumerate(vals):
    ax.text(v + (0.15 if v >= 0 else -0.15), y, f"{v:+.2f}", va="center",
            ha="left" if v >= 0 else "right", color=INK, fontsize=10)
ax.axvline(0, color=MUTED, linewidth=1)
ax.set_xlim(-1.5, 10.5)
ax.set_xlabel("USD per kg H$_2$")
ax.set_title(f"LCOH breakdown, base case: {total:.2f} USD/kg", loc="left", color=INK)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "lcoh_breakdown.png", dpi=160)

# 2) Tornado chart (+/-20 %)
sens = sensitivity(base, 0.2)
order = sorted(sens, key=lambda k: abs(sens[k][1] - sens[k][0]))
fig, ax = plt.subplots(figsize=(8, 3.6))
for y, k in enumerate(order):
    lo, hi = sens[k]
    ax.barh(y, lo - total, left=total, color=BLUE, height=0.55, label="Parameter -20 %" if y == 0 else None)
    ax.barh(y, hi - total, left=total, color=ORANGE, height=0.55, label="Parameter +20 %" if y == 0 else None)
ax.set_yticks(range(len(order)), order)
ax.axvline(total, color=INK, linewidth=1)
ax.set_xlabel("LCOH [USD per kg H$_2$]")
ax.set_title("Sensitivity of LCOH to a ±20 % change in each input", loc="left", color=INK)
ax.legend(frameon=False, loc="lower right")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "lcoh_tornado.png", dpi=160)
print("\nSensitivity (+/-20 %):")
for k in order[::-1]:
    lo, hi = sens[k]
    print(f"  {k:<26} {lo:6.2f} .. {hi:6.2f} USD/kg")

# 3) Cost-reduction pathway from the report's conclusions
steps = [("Base case", base)]
s = replace(base, capex_usd_per_mw=base.capex_usd_per_mw / 10)
steps.append(("Electrolyzer CAPEX ÷10", s))
s = replace(s, plant_factor_ratio=1.4)
steps.append(("+ plant factor +40 %", s))
s = replace(s, electricity_cost=base.electricity_cost * 0.7)
steps.append(("+ PV electricity −30 %", s))
labels = [n for n, _ in steps]
values = [lcoh(v) for _, v in steps]
fig, ax = plt.subplots(figsize=(8, 3.4))
ax.barh(labels[::-1], values[::-1], color=BLUE, height=0.55)
for y, v in enumerate(values[::-1]):
    ax.text(v + 0.15, y, f"{v:.2f}", va="center", color=INK, fontsize=10)
ax.axvline(1.0, color=ORANGE, linewidth=2, linestyle="--")
ax.text(1.15, -0.75, "Chile 2040 target ≈ 1 USD/kg", color=INK, fontsize=9, va="center")
ax.set_ylim(-1.1, len(values) - 0.5)
ax.set_xlabel("LCOH [USD per kg H$_2$]")
ax.set_title("Cumulative cost-reduction scenario", loc="left", color=INK)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "lcoh_scenario.png", dpi=160)
print("\nScenario:")
for n, v in zip(labels, values):
    print(f"  {n:<26} {v:6.2f} USD/kg")
