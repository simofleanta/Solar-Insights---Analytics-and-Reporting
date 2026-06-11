"""Simulation - baza de lucru pe datele Gold (solar grid).

Deocamdata doar ne CONECTAM la SQLite-ul local (solar_grid.db) si incarcam
cele 4 tabele Gold in pandas, ca sa le avem la indemana pentru orice simulare
de pus mai tarziu (what-if surplus/deficit, forecast, economic, Monte Carlo).

Ruleaza:  python simulation.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

# baza de date locala, langa script (o creezi cu gold_to_sqlite.py)
DB_PATH = str(Path(__file__).with_name("solar_grid.db"))

GOLD_TABLES = [
    "gold_generation_vs_consumption",
    "gold_surplus_deficit_zona",
    "gold_top_farms",
    "gold_anomalii_grid",
]


def load_gold(db_path: str = DB_PATH) -> dict[str, pd.DataFrame]:
    """Citeste fiecare tabel Gold din SQLite intr-un DataFrame.
    Returneaza un dict {nume_tabel: DataFrame}.
    """
    conn = sqlite3.connect(db_path)
    try:
        data = {t: pd.read_sql_query(f"SELECT * FROM {t}", conn) for t in GOLD_TABLES}
    finally:
        conn.close()
    return data


def overview(data: dict[str, pd.DataFrame]) -> None:
    """Afiseaza pe scurt ce contine fiecare tabel."""
    for name, df in data.items():
        print("=" * 70)
        print(f"{name}  ->  {df.shape[0]} randuri x {df.shape[1]} coloane")
        print("-" * 70)
        print("Coloane:", list(df.columns))
        print(df.head(3).to_string(index=False))
        print()


class SurplusDeficitMetrics:
    """Sectiunea 1 - metrici de deficit/surplus energetic pe zona.

    Lucreaza pe gold_generation_vs_consumption (lunar, pe zona).
    Fiecare metrica e o metoda separata; summary() le asambleaza intr-un
    tabel agregat anual pe zona.
    """

    def __init__(self, gen: pd.DataFrame):
        self.gen = gen
        # agregare anuala pe zona, baza pentru toate metricile
        self._z = gen.groupby("zona_electrica").agg(
            prod_kwh=("total_productie_kwh", "sum"),
            consum_kwh=("total_consum_kwh", "sum"),
            ore_surplus=("ore_surplus", "sum"),
            ore_deficit=("ore_deficit", "sum"),
            balanta_std=("surplus_deficit_kwh", "std"),
        )

    # --- metrici individuale (toate returneaza o Serie indexata pe zona) ---

    def net_balance(self) -> pd.Series:
        """Balanta neta anuala (kWh): productie - consum. Negativ = deficit."""
        return (self._z["prod_kwh"] - self._z["consum_kwh"]).round(0)

    def coverage_ratio(self) -> pd.Series:
        """Grad de acoperire (%): cat din consum acopera productia locala."""
        return (self._z["prod_kwh"] / self._z["consum_kwh"] * 100).round(2)

    def dependency_index(self) -> pd.Series:
        """Indice de dependenta (%): cat din energie vine din import/retea."""
        return (100 - self.coverage_ratio()).round(2)

    def surplus_hours_share(self) -> pd.Series:
        """% din ore in care zona a fost in surplus (exportatoare)."""
        tot = self._z["ore_surplus"] + self._z["ore_deficit"]
        return (self._z["ore_surplus"] / tot * 100).round(2)

    def balance_volatility(self) -> pd.Series:
        """Volatilitatea balantei (std a surplus/deficit lunar, kWh)."""
        return self._z["balanta_std"].round(0)

    # --- asamblare ---

    def summary(self) -> pd.DataFrame:
        """Tabel agregat anual pe zona cu toate metricile, sortat dupa acoperire."""
        out = pd.DataFrame({
            "balanta_neta_kwh": self.net_balance(),
            "coverage_pct": self.coverage_ratio(),
            "dependency_idx_pct": self.dependency_index(),
            "surplus_hours_share_pct": self.surplus_hours_share(),
            "balance_volatility_kwh": self.balance_volatility(),
        })
        return out.sort_values("coverage_pct", ascending=False).reset_index()


class GenerationPerformanceMetrics:
    """Sectiunea 2 - indici de consum / productie / performanta (LUNAR, pe zona).

    Lucreaza pe gold_generation_vs_consumption.
    - consumption_index / production_index: lunar vs media anuala a zonei (baza 100)
    - performance_index: productie / consum * 100 (prag 100 = acoperire completa)
    - mismatch: cat de dezaliniate sunt sezonalitatea productiei si a consumului
    """

    def __init__(self, gen: pd.DataFrame):
        cols = ["an", "luna", "luna_nume", "zona_electrica",
                "total_productie_kwh", "total_consum_kwh"]
        self.df = gen[cols].copy().sort_values(["zona_electrica", "luna"])
        # baza index = media lunara a fiecarei zone (regula de 3 cu numitorul = media)
        g = self.df.groupby("zona_electrica")
        self._media_consum = g["total_consum_kwh"].transform("mean")
        self._media_prod = g["total_productie_kwh"].transform("mean")

    # --- indici individuali (toti returneaza o Serie aliniata la self.df) ---

    def consumption_index(self) -> pd.Series:
        """Consum lunar vs media zonei (100 = luna medie)."""
        return (self.df["total_consum_kwh"] / self._media_consum * 100).round(1)

    def production_index(self) -> pd.Series:
        """Productie lunara vs media zonei (100 = luna medie)."""
        return (self.df["total_productie_kwh"] / self._media_prod * 100).round(1)

    def performance_index(self) -> pd.Series:
        """Acoperire: productie / consum * 100 (100 = productia acopera consumul)."""
        return (self.df["total_productie_kwh"] / self.df["total_consum_kwh"] * 100).round(1)

    def self_sufficiency_ratio(self) -> pd.Series:
        """Coverage / self-sufficiency ratio: productie / consum, ca raport 0-1.
        E performance_index/100. ATENTIE: NU e Performance Ratio (PR) de inginerie
        PV (acela = energie reala / energie teoretica la iradianta; are nevoie de
        capacitate instalata + iradianta, pe care Gold nu le are)."""
        return (self.df["total_productie_kwh"] / self.df["total_consum_kwh"]).round(3)

    def mismatch(self) -> pd.Series:
        """Dezaliniere sezoniera: index productie - index consum.
        Pozitiv = productie sus / consum jos (potential surplus/risipa).
        Negativ = consum sus / productie jos (presiune pe retea)."""
        return (self.production_index() - self.consumption_index()).round(1)

    # --- asamblare ---

    def summary(self) -> pd.DataFrame:
        """Tabel lunar pe zona cu toti indicii."""
        out = self.df[["an", "luna", "luna_nume", "zona_electrica"]].copy()
        out["consum_idx"] = self.consumption_index()
        out["prod_idx"] = self.production_index()
        out["perf_idx"] = self.performance_index()
        out["mismatch"] = self.mismatch()
        return out.reset_index(drop=True)

    def pivot(self, metric: str = "perf_idx") -> pd.DataFrame:
        """Pivot luna x zona pentru o metrica (perf_idx / consum_idx / prod_idx / mismatch)."""
        s = self.summary()
        return s.pivot(index="luna_nume", columns="zona_electrica", values=metric) \
                .reindex(s.drop_duplicates("luna").sort_values("luna")["luna_nume"])


class MismatchMetrics:
    """Sectiunea 3 - dezalinierea sezoniera productie vs consum (LUNAR, pe zona).

    Mismatch = index_productie - index_consum (din sectiunea 2).
    NU e anomalie/eroare: e decalajul STRUCTURAL intre cand produce soarele
    si cand consuma lumea. Clasifica lunile si arata cine conduce decalajul.
    """

    PRAG = 15  # cat de departe de 0 ca sa numim luna surplus/deficit sezonier

    def __init__(self, gen: pd.DataFrame):
        self.gp = GenerationPerformanceMetrics(gen)
        self._s = self.gp.summary()  # an, luna, luna_nume, zona, consum_idx, prod_idx, perf_idx, mismatch

    def _clasifica(self, m: float) -> str:
        if m > self.PRAG:
            return "SURPLUS"      # productie sus / consum jos
        if m < -self.PRAG:
            return "DEFICIT"      # consum sus / productie jos
        return "ECHILIBRU"

    # --- metrici ---

    def monthly(self) -> pd.DataFrame:
        """Tabel lunar pe zona cu mismatch, magnitudine si clasificare."""
        out = self._s[["an", "luna", "luna_nume", "zona_electrica", "mismatch"]].copy()
        out["abs_mismatch"] = out["mismatch"].abs().round(1)
        out["tip"] = out["mismatch"].apply(self._clasifica)
        return out.reset_index(drop=True)

    def magnitude(self) -> pd.Series:
        """|mismatch| - cat de departe de echilibru, indiferent de directie."""
        return self._s["mismatch"].abs()

    def drivers(self) -> pd.DataFrame:
        """Cine conduce decalajul: amplitudinea sezoniera (max-min) a fiecarui
        index, pe zona. Amplitudine mare = factor dominant."""
        g = self._s.groupby("zona_electrica")
        amp = pd.DataFrame({
            "amp_productie": (g["prod_idx"].max() - g["prod_idx"].min()).round(0),
            "amp_consum": (g["consum_idx"].max() - g["consum_idx"].min()).round(0),
        })
        amp["raport_prod_vs_consum"] = (amp["amp_productie"] / amp["amp_consum"]).round(1)
        return amp.reset_index()

    def extremes(self) -> pd.DataFrame:
        """Pentru fiecare zona: luna cea mai echilibrata (|mismatch| minim)
        si cea mai dezaliniata (|mismatch| maxim)."""
        m = self.monthly()
        rows = []
        for z, sub in m.groupby("zona_electrica"):
            best = sub.loc[sub["abs_mismatch"].idxmin()]
            worst = sub.loc[sub["abs_mismatch"].idxmax()]
            rows.append({
                "zona_electrica": z,
                "luna_echilibru": best["luna_nume"], "mismatch_min": best["mismatch"],
                "luna_extrem": worst["luna_nume"], "mismatch_max": worst["mismatch"],
            })
        return pd.DataFrame(rows)


class IntradayProfile:
    """Sectiunea 4 - profil ORAR (6-19) din gold_anomalii_grid.

    ATENTIE la natura datelor: tabelul contine doar orele 6-19 (lumina zilei)
    si DOAR randuri de status DEFICIT. Deci NU e profil zi/noapte complet -
    e profilul de zi, in care chiar si la varf de soare productia nu acopera
    consumul. Util ca sa vezi cele doua varfuri de consum (dimineata/seara)
    fata de varful de productie (pranz).
    """

    def __init__(self, anomalii: pd.DataFrame):
        self.df = anomalii

    def hourly_avg(self) -> pd.DataFrame:
        """Medie pe ora (toate zonele): productie, consum, deficit, acoperire %."""
        g = self.df.groupby("ora").agg(
            productie=("total_productie_kwh", "mean"),
            consum=("total_consum_kwh", "mean"),
            deficit=("surplus_deficit_kwh", "mean"),
        ).round(0)
        g["acoperire_pct"] = (g["productie"] / g["consum"] * 100).round(1)
        return g.reset_index()

    def peak_hours(self) -> dict:
        """Orele de varf: productie maxima, consum maxim, deficit cel mai adanc."""
        h = self.hourly_avg()
        return {
            "varf_productie": int(h.loc[h["productie"].idxmax(), "ora"]),
            "varf_consum": int(h.loc[h["consum"].idxmax(), "ora"]),
            "deficit_maxim": int(h.loc[h["deficit"].idxmin(), "ora"]),
            "acoperire_maxima_pct": float(h["acoperire_pct"].max()),
        }

    def coverage_by_zone_hour(self) -> pd.DataFrame:
        """Pivot ora x zona cu acoperirea % (productie/consum)."""
        z = self.df.groupby(["ora", "zona_electrica"]).agg(
            prod=("total_productie_kwh", "sum"),
            cons=("total_consum_kwh", "sum"),
        )
        z["acoperire_pct"] = (z["prod"] / z["cons"] * 100).round(1)
        return z["acoperire_pct"].unstack()


if __name__ == "__main__":
    gold = load_gold()

    # Acces individual pentru lucru ulterior:
    gen = gold["gold_generation_vs_consumption"]
    zona = gold["gold_surplus_deficit_zona"]
    farms = gold["gold_top_farms"]
    anomalii = gold["gold_anomalii_grid"]

    print("=" * 70)
    print("SECTIUNEA 1 - Deficit / Surplus energetic (anual, pe zona)")
    print("=" * 70)
    sd = SurplusDeficitMetrics(gen)
    print(sd.summary().to_string(index=False))

    print()
    print("=" * 70)
    print("SECTIUNEA 2 - Indici consum / productie / performanta (lunar)")
    print("=" * 70)
    gp = GenerationPerformanceMetrics(gen)
    print("\n-- Index de PERFORMANTA (productie/consum %, prag 100) --")
    print(gp.pivot("perf_idx").round(1).to_string())
    print("\n-- MISMATCH (index prod - index consum) --")
    print(gp.pivot("mismatch").round(1).to_string())

    print()
    print("=" * 70)
    print("SECTIUNEA 3 - Mismatch sezonier (cine conduce decalajul)")
    print("=" * 70)
    mm = MismatchMetrics(gen)
    print("\n-- Cine CONDUCE decalajul (amplitudine sezoniera index) --")
    print(mm.drivers().to_string(index=False))
    print("\n-- Luna de echilibru vs luna de extrem, pe zona --")
    print(mm.extremes().to_string(index=False))
