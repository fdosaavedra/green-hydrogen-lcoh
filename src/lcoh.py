"""Levelized Cost of Hydrogen (LCOH) model for PV-powered PEM electrolysis.

Implements the LCOH equation used in the 2021 IPre research project
(based on GIZ, 2019), with reference values for the Atacama region, Chile:

    LCOH = P_inst * I * (FRC + M(fp)) / (h * fp * Q_H2)
           + Q_H2O * P_H2O + Q_e * P_e - Q_O2 * P_O2

All results are in USD per kg of hydrogen.
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class LCOHInputs:
    p_inst_mw: float = 1.25            # installed electrolyzer power [MW]
    capex_usd_per_mw: float = 1.5e6    # electrolyzer investment, high-investment scenario [USD/MW]
    annuity_factor: float = 4.6967e-6  # (FRC + M(fp)) / (h * fp * Q_H2) at the reference plant factor [1/kg]
    plant_factor_ratio: float = 1.0    # plant factor relative to the reference case (1.0 = baseline)
    water_cost: float = 0.0238         # Q_H2O * P_H2O [USD/kg]
    electricity_cost: float = 2.8713   # Q_e * P_e, PV electricity for electrolysis [USD/kg]
    oxygen_credit: float = 0.234       # Q_O2 * P_O2, sale of by-product oxygen [USD/kg]


def capital_term(x: LCOHInputs) -> float:
    """Annualized electrolyzer capital + maintenance per kg of H2.

    Production scales with the plant factor, so the per-kg capital cost
    scales with 1 / fp (maintenance is kept proportional, a simplification).
    """
    return x.p_inst_mw * x.capex_usd_per_mw * x.annuity_factor / x.plant_factor_ratio


def breakdown(x: LCOHInputs) -> dict:
    return {
        "Electrolyzer capital + O&M": capital_term(x),
        "PV electricity": x.electricity_cost,
        "Water": x.water_cost,
        "Oxygen by-product credit": -x.oxygen_credit,
    }


def lcoh(x: LCOHInputs) -> float:
    return sum(breakdown(x).values())


# Parameters varied in the sensitivity analysis, mapped to how a relative
# change of +/- delta is applied to the inputs.
def _scale(field):
    return lambda x, f: replace(x, **{field: getattr(x, field) * f})


SENSITIVITY_PARAMS = {
    "Electrolyzer CAPEX (I)": _scale("capex_usd_per_mw"),
    "PV plant factor (fp)": _scale("plant_factor_ratio"),
    "PV electricity cost (Pe)": _scale("electricity_cost"),
    "Water cost": _scale("water_cost"),
    "Oxygen price": _scale("oxygen_credit"),
}


def sensitivity(x: LCOHInputs, delta: float = 0.2) -> dict:
    """LCOH at (1 - delta) and (1 + delta) of each parameter."""
    return {name: (lcoh(fn(x, 1 - delta)), lcoh(fn(x, 1 + delta)))
            for name, fn in SENSITIVITY_PARAMS.items()}
