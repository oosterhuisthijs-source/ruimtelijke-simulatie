import numpy as np
import pandas as pd
from minisom import MiniSom

from app.config import settings

# All usable numeric columns with sufficient variance in the dataset
SOM_COLUMNS = [
    # Demografie
    "aantal_inwoners_sum",
    "aantal_mannen_sum",
    "aantal_vrouwen_sum",
    "aantal_inwoners_0_tot_15_jaar_sum",
    "aantal_inwoners_15_tot_25_jaar_sum",
    "aantal_inwoners_25_tot_45_jaar_sum",
    "aantal_inwoners_45_tot_65_jaar_sum",
    "aantal_inwoners_65_jaar_en_ouder_sum",
    "aantal_geboorten_sum",
    "aantal_part_huishoudens_sum",
    "aantal_eenpersoonshuishoudens_sum",
    "aantal_eenouderhuishoudens_sum",
    "aantal_tweeouderhuishoudens_sum",
    "aantal_meerpersoonshuishoudens_zonder_kind_sum",
    # Wonen
    "aantal_woningen_sum",
    "aantal_huurwoningen_in_bezit_woningcorporaties_sum",
    "aantal_niet_bewoonde_woningen_sum",
    "aantal_meergezins_woningen_sum",
    "aantal_woningen_bouwjaar_voor_1945_sum",
    "aantal_woningen_bouwjaar_45_tot_65_sum",
    "aantal_woningen_bouwjaar_65_tot_75_sum",
    "aantal_woningen_bouwjaar_75_tot_85_sum",
    "aantal_woningen_bouwjaar_85_tot_95_sum",
    "aantal_woningen_bouwjaar_95_tot_05_sum",
    "aantal_woningen_bouwjaar_05_tot_15_sum",
    "aantal_woningen_bouwjaar_15_en_later_sum",
    "gemiddelde_woz_waarde_woning_area_weighted_average",
    "gemiddelde_huishoudensgrootte_area_weighted_average",
    "percentage_huurwoningen_area_weighted_average",
    "percentage_koopwoningen_area_weighted_average",
    # Sociaal-economisch
    "aantal_personen_met_uitkering_onder_aowlft_sum",
    "percentage_geb_nederland_herkomst_nederland_area_weighted_average",
    "percentage_geb_nederland_herkomst_buiten_europa_area_weighted_average",
    "percentage_geb_nederland_herkomst_overig_europa_area_weighted_average",
    "percentage_geb_buiten_nederland_herkomst_europa_area_weighted_average",
    "percentage_geb_buiten_nederland_herkmst_buiten_europa_area_weighted_average",
    # Gebouwfuncties
    "num_woonfunctie",
    "num_kantoorfunctie",
    "num_industriefunctie",
    "num_winkelfunctie",
    "num_onderwijsfunctie",
    "num_gezondheidszorgfunctie",
    "num_sportfunctie",
    "num_logiesfunctie",
    "num_bijeenkomstfunctie",
    "num_celfunctie",
    "num_overige_gebruiksfunctie",
    # Landgebruik — bebouwing
    "bebouwing_in_primair_bebouwd_gebied_fraction",
    "bebouwing_in_secundair_bebouwd_gebied_fraction",
    "bebouwing_in_buitengebied_fraction",
    "hoofdinfrastructuur_en_spoorbaanlichamen_fraction",
    "smalle_wegen_fraction",
    "halfverharde_wegen_infrastructuur_langzaam_verkeer_en_overige_infrastructuur_fraction",
    # Landgebruik — natuur en groen
    "loofbos_fraction",
    "naaldbos_fraction",
    "bos_in_moerasgebied_fraction",
    "bos_in_primair_bebouwd_gebied_fraction",
    "bos_in_secundair_bebouwd_gebied_fraction",
    "heide_fraction",
    "matig_vergraste_heide_fraction",
    "sterk_vergraste_heide_fraction",
    "duinheide_fraction",
    "duinen_met_hoge_vegetatie_fraction",
    "duinen_met_lage_vegetatie_fraction",
    "gras_in_primair_bebouwd_gebied_fraction",
    "gras_in_secundair_bebouwd_gebied_fraction",
    "gras_in_het_kustgebied_fraction",
    "overig_gras_fraction",
    "agrarisch_gras_fraction",
    "natuurlijk_beheerde_agrarische_graslanden_fraction",
    "rietvegetatie_fraction",
    "overige_moeras_vegetatie_fraction",
    "struikvegetatie_in_moerasgebied_hoog_fraction",
    "struikvegetatie_in_moerasgebied_laag_fraction",
    "overige_struikvegetatie_hoog_fraction",
    "overige_struikvegetatie_laag_fraction",
    "kwelders_fraction",
    "zoet_water_fraction",
    "zout_water_fraction",
    "open_stuifzand_en_of_rivierzand_fraction",
    "open_zand_in_kustgebied_fraction",
    "overig_grondgebruik_in_buitengebied_fraction",
    # Landgebruik — landbouw
    "agrarisch_gras_fraction",
    "granen_fraction",
    "maïs_fraction",
    "aardappelen_fraction",
    "bieten_fraction",
    "glastuinbouw_fraction",
    "bloembollen_fraction",
    "boomgaarden_fraction",
    "fruitkwekerijen_fraction",
    "boomkwekerijen_fraction",
    "overige_landbouwgewassen_fraction",
    "zonneparken_fraction",
    # Milieu en klimaat
    "geluid_lden",
    "groundheight",
    "hitte",
    "lichtemissie",
    "flooddepth_1",
    "flooddepth_2",
    "flooddepth_3",
    "flooddepth_4",
    "flooddepth_5",
]


# Key variables to include in cluster map for tooltips
TOOLTIP_COLUMNS = [
    "gemeentenaam",
    "wijknaam",
    "aantal_inwoners_sum",
    "gemiddelde_woz_waarde_woning_area_weighted_average",
    "hitte",
    "geluid_lden",
    "bebouwing_in_primair_bebouwd_gebied_fraction",
]


class SOMService:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.som = None
        self.trained = False
        self.feature_matrix = None
        self.h3_ids = None
        self._cluster_cache: dict[int, list[dict]] = {}  # year → cluster list

    async def train(self):
        """Train SOM on all hexagons for year 2023."""
        df_2023 = self.df[self.df["year_int"] == 2023].copy()

        available = [c for c in SOM_COLUMNS if c in df_2023.columns]
        features = df_2023[available].fillna(0).values

        col_max = features.max(axis=0)
        col_max[col_max == 0] = 1
        self.feature_matrix = features / col_max
        self.h3_ids = df_2023["h3_id"].values

        self.som = MiniSom(
            x=settings.som_grid_x,
            y=settings.som_grid_y,
            input_len=len(available),
            sigma=1.5,
            learning_rate=0.5,
            random_seed=42,
        )
        self.som.random_weights_init(self.feature_matrix)
        self.som.train(self.feature_matrix, settings.som_iterations)
        self.trained = True

        # Precompute 2023 cluster map
        self._cluster_cache[2023] = self._compute_cluster_map(df_2023)

    def _compute_cluster_map(self, df_year: pd.DataFrame) -> list[dict]:
        """Compute cluster assignments for a given year's DataFrame."""
        available = [c for c in SOM_COLUMNS if c in df_year.columns]
        features = df_year[available].fillna(0).values.astype(float)
        col_max = self.feature_matrix.max(axis=0)
        col_max[col_max == 0] = 1
        features_norm = features / col_max

        # Build tooltip lookup
        tooltip_cols = [c for c in TOOLTIP_COLUMNS if c in df_year.columns]
        tooltip_data = df_year[tooltip_cols].to_dict(orient="records")

        results = []
        for i, vec in enumerate(features_norm):
            x, y = self.som.winner(vec)
            entry = {
                "h3": df_year["h3_id"].iloc[i],
                "cluster_x": int(x),
                "cluster_y": int(y),
                "cluster_id": int(x * settings.som_grid_y + y),
            }
            # Add tooltip fields with rounding for floats, None for NaN
            for col in tooltip_cols:
                val = tooltip_data[i].get(col)
                if val is None:
                    entry[col] = None
                elif isinstance(val, float):
                    import math
                    entry[col] = None if math.isnan(val) else round(val, 1)
                else:
                    entry[col] = val
            results.append(entry)
        return results

    def get_cluster_map(self) -> list[dict]:
        """Return cluster map for 2023 (cached)."""
        return self._cluster_cache.get(2023, [])

    def get_cluster_map_for_year(self, year: int) -> list[dict]:
        """Return cluster map for any year, with lazy caching."""
        if year in self._cluster_cache:
            return self._cluster_cache[year]
        if not self.trained:
            return []
        df_year = self.df[self.df["year_int"] == year].copy()
        if df_year.empty:
            return []
        result = self._compute_cluster_map(df_year)
        self._cluster_cache[year] = result
        return result

    def project_trend(self, target_year: int) -> tuple[np.ndarray, np.ndarray]:
        """Project all hexagon features to target_year using linear trend from 2018-2023."""
        available = [c for c in SOM_COLUMNS if c in self.df.columns]
        years = sorted(self.df["year_int"].unique())
        year_arr = np.array(years, dtype=float)
        n = len(year_arr)
        sum_x = year_arr.sum()
        sum_x2 = (year_arr ** 2).sum()

        # Pivot: index=h3_id, columns=year_int — for all SOM columns at once
        df_2023 = self.df[self.df["year_int"] == 2023]
        h3_ids = df_2023["h3_id"].values

        projected = np.zeros((len(h3_ids), len(available)), dtype=float)

        for j, col in enumerate(available):
            pivot = (
                self.df.pivot_table(index="h3_id", columns="year_int", values=col, aggfunc="first")
                .reindex(index=h3_ids)
            )
            vals = pivot.reindex(columns=years).values  # (n_hex, n_years)

            # Vectorized OLS per hexagon, handling NaN via nansum
            mask = (~np.isnan(vals)).astype(float)  # (n_hex, n_years)
            n_valid = mask.sum(axis=1)
            n_valid[n_valid == 0] = 1  # avoid division by zero

            vals_filled = np.where(np.isnan(vals), 0.0, vals)
            sum_y = (vals_filled * mask).sum(axis=1)
            sum_xy = (vals_filled * mask * year_arr).sum(axis=1)
            sum_x_valid = (mask * year_arr).sum(axis=1)
            sum_x2_valid = (mask * year_arr ** 2).sum(axis=1)

            denom = n_valid * sum_x2_valid - sum_x_valid ** 2
            denom[denom == 0] = 1

            slope = (n_valid * sum_xy - sum_x_valid * sum_y) / denom
            intercept = (sum_y - slope * sum_x_valid) / n_valid

            projected[:, j] = np.clip(intercept + slope * target_year, 0, 255)

        col_max = self.feature_matrix.max(axis=0)
        col_max[col_max == 0] = 1
        features_norm = projected / col_max

        return features_norm, h3_ids

    def get_trajectory(self, h3_id: str) -> list[dict]:
        """Return SOM cluster per year for a single hexagon."""
        hex_data = self.df[self.df["h3_id"] == h3_id].sort_values("year_int")
        available = [c for c in SOM_COLUMNS if c in hex_data.columns]

        trajectory = []
        for _, row in hex_data.iterrows():
            vec = row[available].fillna(0).values.astype(float)
            col_max = self.feature_matrix.max(axis=0)
            col_max[col_max == 0] = 1
            vec_norm = vec / col_max
            x, y = self.som.winner(vec_norm)
            trajectory.append({
                "year": int(row["year_int"]),
                "cluster_x": int(x),
                "cluster_y": int(y),
                "cluster_id": int(x * settings.som_grid_y + y),
            })
        return trajectory
