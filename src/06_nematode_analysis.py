"""Resume los datos preparados de nematodos y genera la salida pública de la web.

Este código no vuelve a interpretar el Excel. Lee únicamente las tablas validadas
por 05_prepare_nematode_data.py y mantiene todos los resultados en processed/.
"""
from __future__ import annotations

import csv
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "processed" / "nematodos_analisis_listo"
SUMMARY = INPUT / "resumenes"
WEB = INPUT / "web"

IDENTITY = ["finca_id", "tratamiento", "lote", "parcela", "productor_finca"]
ABUNDANCE_UNIT = "individuos/100 cm³ de suelo"
PARAMETER_VARIABLES = {
    "abundancia_en_1_ml": ("Abundancia observada en 1 ml", "individuos/mL"),
    "volumen_contado_abundancia_ml": ("Volumen contado para abundancia", "mL"),
    "volumen_agregado_identificacion_ml": ("Volumen agregado para identificación", "mL"),
    "total_individuos_identificados": ("Total de individuos identificados", "individuos"),
    "abundancia_total_ninja": ("Abundancia total usada por NINJA", ABUNDANCE_UNIT),
}
NINJA_VARIABLES = {
    "mi": ("indices_ninja", "Índice de madurez (MI)", "índice"),
    "mi2_5": ("indices_ninja", "Índice de madurez 2–5 (MI2-5)", "índice"),
    "smi": ("indices_ninja", "Índice SMI", "índice"),
    "ppi": ("indices_ninja", "Índice de parásitos de plantas (PPI)", "índice"),
    "ci": ("indices_ninja", "Índice de canal (CI)", "índice 0–100"),
    "bi": ("indices_ninja", "Índice basal (BI)", "índice 0–100"),
    "ei": ("indices_ninja", "Índice de enriquecimiento (EI)", "índice 0–100"),
    "si": ("indices_ninja", "Índice de estructura (SI)", "índice 0–100"),
    "total_biomass_mg": ("huellas_ninja", "Biomasa total", "mg"),
    "cft": ("huellas_ninja", "CFT (NINJA)", "unidad no indicada en la fuente"),
    "eft": ("huellas_ninja", "EFT (NINJA)", "unidad no indicada en la fuente"),
    "sft": ("huellas_ninja", "SFT (NINJA)", "unidad no indicada en la fuente"),
    "heft": ("huellas_ninja", "HeFT (NINJA)", "unidad no indicada en la fuente"),
    "fuft": ("huellas_ninja", "FuFT (NINJA)", "unidad no indicada en la fuente"),
    "baft": ("huellas_ninja", "BaFT (NINJA)", "unidad no indicada en la fuente"),
    "prft": ("huellas_ninja", "PrFT (NINJA)", "unidad no indicada en la fuente"),
    "unicellular_eucaryote_feeder_footprint": (
        "huellas_ninja", "Huella de consumidores de eucariotas unicelulares", "unidad no indicada en la fuente"
    ),
    "omnivore_footprint": ("huellas_ninja", "Huella de omnívoros", "unidad no indicada en la fuente"),
    "total_number_ind": ("huellas_ninja", "Número total de individuos (NINJA)", ABUNDANCE_UNIT),
    "herbivores_pct_of_total": ("porcentajes_ninja", "Herbívoros del total", "%"),
    "fungivores_pct_of_total": ("porcentajes_ninja", "Fungívoros del total", "%"),
    "fungivores_pct_of_free_living": ("porcentajes_ninja", "Fungívoros de vida libre", "%"),
    "bacterivores_pct_of_total": ("porcentajes_ninja", "Bacterívoros del total", "%"),
    "bacterivores_pct_of_free_living": ("porcentajes_ninja", "Bacterívoros de vida libre", "%"),
    "predators_pct_of_total": ("porcentajes_ninja", "Depredadores del total", "%"),
    "predators_pct_of_free_living": ("porcentajes_ninja", "Depredadores de vida libre", "%"),
    "unicellular_eucaryote_feeders_pct_of_total": (
        "porcentajes_ninja", "Consumidores de eucariotas unicelulares del total", "%"
    ),
    "unicellular_eucaryote_feeders_pct_of_free_living": (
        "porcentajes_ninja", "Consumidores de eucariotas unicelulares de vida libre", "%"
    ),
    "omnivores_pct_of_total": ("porcentajes_ninja", "Omnívoros del total", "%"),
    "omnivores_pct_of_free_living": ("porcentajes_ninja", "Omnívoros de vida libre", "%"),
    "sedentary_parasites_pct_of_herbivores": (
        "porcentajes_ninja", "Parásitos sedentarios de los herbívoros", "%"
    ),
    "migratory_endoparasites_pct_of_herbivores": (
        "porcentajes_ninja", "Endoparásitos migratorios de los herbívoros", "%"
    ),
    "semi_endoparasites_pct_of_herbivores": (
        "porcentajes_ninja", "Semiendoparásitos de los herbívoros", "%"
    ),
    "ectoparasites_pct_of_herbivores": ("porcentajes_ninja", "Ectoparásitos de los herbívoros", "%"),
    "epidermal_root_hair_feeders_pct_of_herbivores": (
        "porcentajes_ninja", "Consumidores de epidermis y pelos radicales de los herbívoros", "%"
    ),
    "algal_lichen_moss_feeders_pct_of_herbivores": (
        "porcentajes_ninja", "Consumidores de algas, líquenes y musgos de los herbívoros", "%"
    ),
    "cp_1_pct_of_free_living": ("porcentajes_ninja", "c-p 1 de vida libre", "%"),
    "cp_2_pct_of_free_living": ("porcentajes_ninja", "c-p 2 de vida libre", "%"),
    "cp_3_pct_of_free_living": ("porcentajes_ninja", "c-p 3 de vida libre", "%"),
    "cp_4_pct_of_free_living": ("porcentajes_ninja", "c-p 4 de vida libre", "%"),
    "cp_5_pct_of_free_living": ("porcentajes_ninja", "c-p 5 de vida libre", "%"),
    "pp_2_pct_of_herbivores": ("porcentajes_ninja", "p-p 2 de los herbívoros", "%"),
    "pp_3_pct_of_herbivores": ("porcentajes_ninja", "p-p 3 de los herbívoros", "%"),
    "pp_4_pct_of_herbivores": ("porcentajes_ninja", "p-p 4 de los herbívoros", "%"),
    "pp_5_pct_of_herbivores": ("porcentajes_ninja", "p-p 5 de los herbívoros", "%"),
}
GROUP_NAMES = {
    "Herbivores": "Herbívoros",
    "Fungivores": "Fungívoros",
    "Bacterivores": "Bacterívoros",
    "Predators": "Depredadores",
    "Omnivores": "Omnívoros",
}


def clean_text(value: object) -> str:
    return "" if value is None else re.sub(r"\s+", " ", str(value)).strip()


def slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", clean_text(value)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def number(value: object, context: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: valor no numérico {value!r}.") from error
    if not math.isfinite(result):
        raise ValueError(f"{context}: valor no finito {value!r}.")
    return result


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Ejecuta primero python src/05_prepare_nematode_data.py."
        )
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"{path.name}: faltan columnas requeridas: {missing}.")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name} no contiene filas.")
    return rows


def identity(row: dict[str, str]) -> dict[str, object]:
    treatment = clean_text(row["tratamiento"])
    lot = str(int(row["lote"]))
    farm = int(row["finca_id"])
    parcel = clean_text(row["parcela"])
    if treatment not in {"Pina", "Bosque"} or parcel != f"{treatment}_{lot}" or farm <= 0:
        raise ValueError(f"Identificación de parcela inválida: {row}.")
    return {
        "finca_id": farm,
        "tratamiento": treatment,
        "lote": lot,
        "parcela": parcel,
        "productor_finca": clean_text(row["productor_finca"]),
    }


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    abundance = read_csv(
        INPUT / "abundancia_taxones.csv",
        set(IDENTITY) | {
            "taxon", "conteo_identificacion", "estado_conteo",
            "abundancia_absoluta", "abundancia_relativa",
        },
    )
    traits = read_csv(
        INPUT / "rasgos_taxones.csv",
        {"taxon", "grupo_alimenticio", "clase_cp", "clase_pp", "masa_ug"},
    )
    indices = read_csv(
        INPUT / "indices_ninja_por_parcela.csv",
        set(IDENTITY) | set(NINJA_VARIABLES),
    )
    ninja_columns = set(indices[0]) - set(IDENTITY) - {"muestra_origen"}
    if ninja_columns != set(NINJA_VARIABLES):
        missing = sorted(set(NINJA_VARIABLES) - ninja_columns)
        unexpected = sorted(ninja_columns - set(NINJA_VARIABLES))
        raise ValueError(
            "Las variables de indices_ninja_por_parcela.csv no coinciden con las 45 "
            f"variables NINJA esperadas. Faltantes: {missing}; no reconocidas: {unexpected}."
        )
    parameters = read_csv(
        INPUT / "parametros_muestras.csv",
        set(IDENTITY) | set(PARAMETER_VARIABLES),
    )

    trait_by_taxon: dict[str, dict[str, str]] = {}
    for row in traits:
        taxon = clean_text(row["taxon"])
        if not taxon or taxon in trait_by_taxon:
            raise ValueError(f"Taxón vacío o duplicado en rasgos_taxones.csv: {taxon!r}.")
        source_group = clean_text(row["grupo_alimenticio"]).split(" - ", 1)[0]
        if source_group not in GROUP_NAMES:
            raise ValueError(f"Grupo alimenticio no reconocido para {taxon}: {source_group!r}.")
        trait_by_taxon[taxon] = {**row, "grupo_resumido": GROUP_NAMES[source_group]}

    parcel_meta: dict[str, dict[str, object]] = {}
    abundance_by_parcel: dict[str, dict[str, float]] = defaultdict(dict)
    relative_by_parcel: dict[str, dict[str, float]] = defaultdict(dict)
    count_by_parcel: dict[str, dict[str, float | None]] = defaultdict(dict)
    state_by_parcel_taxon: dict[tuple[str, str], str] = {}
    expected_taxa: set[str] | None = None
    for row in abundance:
        meta = identity(row)
        parcel = str(meta["parcela"])
        taxon = clean_text(row["taxon"])
        if taxon not in trait_by_taxon:
            raise ValueError(f"{taxon!r} no aparece en rasgos_taxones.csv.")
        if taxon in abundance_by_parcel[parcel]:
            raise ValueError(f"Resultado duplicado para {parcel}, {taxon}.")
        value = number(row["abundancia_absoluta"], f"Abundancia de {taxon} en {parcel}")
        if value < 0:
            raise ValueError(f"Abundancia negativa para {parcel}, {taxon}.")
        if parcel in parcel_meta and parcel_meta[parcel] != meta:
            raise ValueError(f"Metadatos discordantes para {parcel}.")
        parcel_meta[parcel] = meta
        abundance_by_parcel[parcel][taxon] = value
        relative = number(row["abundancia_relativa"], f"Abundancia relativa de {taxon} en {parcel}")
        if relative < 0 or relative > 1 + 1e-9:
            raise ValueError(f"Abundancia relativa fuera de rango para {parcel}, {taxon}.")
        relative_by_parcel[parcel][taxon] = relative
        state = clean_text(row["estado_conteo"])
        if state == "reportado":
            count = number(row["conteo_identificacion"], f"Conteo de {taxon} en {parcel}")
            if count < 0:
                raise ValueError(f"Conteo negativo para {parcel}, {taxon}.")
        elif state == "no_reportado_tratado_como_cero_en_fuente" and row["conteo_identificacion"] == "":
            count = None
        else:
            raise ValueError(f"Estado de conteo inválido para {parcel}, {taxon}: {state!r}.")
        count_by_parcel[parcel][taxon] = count
        state_by_parcel_taxon[(parcel, taxon)] = state

    for parcel, values in abundance_by_parcel.items():
        taxa = set(values)
        expected_taxa = taxa if expected_taxa is None else expected_taxa
        if taxa != expected_taxa:
            raise ValueError(f"{parcel} no contiene el mismo conjunto de taxones que las demás parcelas.")
    if expected_taxa != set(trait_by_taxon):
        raise ValueError("Los taxones de abundancia y rasgos no coinciden.")

    index_by_parcel: dict[str, dict[str, str]] = {}
    for row in indices:
        meta = identity(row)
        parcel = str(meta["parcela"])
        if parcel in index_by_parcel:
            raise ValueError(f"Índices duplicados para {parcel}.")
        if parcel not in parcel_meta or parcel_meta[parcel] != meta:
            raise ValueError(f"Los metadatos de índices no coinciden para {parcel}.")
        index_by_parcel[parcel] = row
    if set(index_by_parcel) != set(parcel_meta):
        raise ValueError("Las parcelas de abundancia e índices no coinciden.")

    parameter_by_parcel: dict[str, dict[str, str]] = {}
    for row in parameters:
        meta = identity(row)
        parcel = str(meta["parcela"])
        if parcel in parameter_by_parcel:
            raise ValueError(f"Parámetros duplicados para {parcel}.")
        if parcel not in parcel_meta or parcel_meta[parcel] != meta:
            raise ValueError(f"Los metadatos de parámetros no coinciden para {parcel}.")
        parameter_by_parcel[parcel] = row
    if set(parameter_by_parcel) != set(parcel_meta):
        raise ValueError("Las parcelas de abundancia y parámetros no coinciden.")

    summary_rows: list[dict[str, object]] = []
    group_rows: list[dict[str, object]] = []
    public_rows: list[dict[str, object]] = []
    public_values: dict[tuple[str, str, str], float | None] = {}

    def add_public(
        meta: dict[str, object], family: str, variable: str, label: str,
        unit: str, value: float | None, detail: str = "", state: str = "reportado",
    ) -> None:
        parcel = str(meta["parcela"])
        key = (parcel, family, variable)
        if key in public_values:
            raise ValueError(f"Variable pública duplicada: {key}.")
        public_values[key] = value
        if state == "reportado" and value is None:
            raise ValueError(f"La variable pública {key} está reportada pero no tiene valor.")
        if state != "reportado" and value is not None:
            raise ValueError(f"La variable pública {key} tiene valor y estado {state!r}.")
        public_rows.append({
            **meta, "familia": family, "variable": variable, "etiqueta": label,
            "unidad": unit, "valor": "" if value is None else value, "estado": state, "detalle": detail,
        })

    group_names = list(GROUP_NAMES.values())
    for parcel in sorted(parcel_meta, key=lambda value: (int(parcel_meta[value]["finca_id"]), parcel_meta[value]["tratamiento"])):
        meta = parcel_meta[parcel]
        values = abundance_by_parcel[parcel]
        total = sum(values.values())
        if total <= 0:
            raise ValueError(f"La abundancia total de {parcel} no es positiva.")
        ninja_total = number(index_by_parcel[parcel]["total_number_ind"], f"Total NINJA de {parcel}")
        if not math.isclose(total, ninja_total, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"La abundancia total no coincide con NINJA para {parcel}.")
        richness = sum(value > 0 for value in values.values())
        for taxon, absolute in values.items():
            expected_relative = absolute / total
            if not math.isclose(relative_by_parcel[parcel][taxon], expected_relative, rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError(f"La abundancia relativa no coincide para {parcel}, {taxon}.")
        ninja_values = {
            code: number(index_by_parcel[parcel][code], f"{code} de {parcel}")
            for code in NINJA_VARIABLES
        }
        summary_rows.append({
            **meta, "abundancia_total": total, "riqueza_taxones": richness, **ninja_values,
        })
        add_public(meta, "indicadores", "abundancia_total", "Abundancia total", ABUNDANCE_UNIT, total)
        add_public(meta, "indicadores", "riqueza_taxones", "Riqueza observada", "taxones con abundancia mayor que cero", float(richness))
        for code, (label, unit) in PARAMETER_VARIABLES.items():
            value = number(parameter_by_parcel[parcel][code], f"{label} de {parcel}")
            if value < 0:
                raise ValueError(f"{label} negativo para {parcel}.")
            add_public(meta, "parametros_muestra", code, label, unit, value)
        for code, (family, label, unit) in NINJA_VARIABLES.items():
            add_public(meta, family, code, label, unit, ninja_values[code])

        totals_by_group = {group: 0.0 for group in group_names}
        for taxon, value in values.items():
            totals_by_group[trait_by_taxon[taxon]["grupo_resumido"]] += value
            trait = trait_by_taxon[taxon]
            source_note = (
                " · conteo no reportado; la fuente lo trató como cero"
                if state_by_parcel_taxon[(parcel, taxon)] != "reportado" else ""
            )
            detail = (
                f"{trait['grupo_alimenticio']} · c-p {trait['clase_cp']} · "
                f"p-p {trait['clase_pp']} · masa {trait['masa_ug']} µg{source_note}"
            )
            add_public(
                meta, "taxones_abundancia", slug(taxon), taxon, ABUNDANCE_UNIT, value, detail,
            )
            add_public(
                meta, "taxones_composicion", slug(taxon), taxon, "% de la abundancia total",
                relative_by_parcel[parcel][taxon] * 100, detail,
            )
            count = count_by_parcel[parcel][taxon]
            add_public(
                meta, "taxones_conteos", slug(taxon), taxon, "individuos contados para identificación",
                count, detail,
                "reportado" if count is not None else "no_reportado",
            )
        for group in group_names:
            absolute = totals_by_group[group]
            percentage = absolute / total * 100
            variable = slug(group)
            group_rows.append({
                **meta, "grupo_alimenticio": group, "abundancia_absoluta": absolute,
                "porcentaje_abundancia": percentage,
            })
            add_public(meta, "grupos_abundancia", variable, group, ABUNDANCE_UNIT, absolute)
            add_public(meta, "grupos_composicion", variable, group, "% de la abundancia total", percentage)

    taxon_summary_rows: list[dict[str, object]] = []
    for taxon in sorted(expected_taxa or []):
        values = [abundance_by_parcel[parcel][taxon] for parcel in parcel_meta]
        nonreported = sum(
            state_by_parcel_taxon[(parcel, taxon)] != "reportado" for parcel in parcel_meta
        )
        taxon_summary_rows.append({
            "taxon": taxon,
            "grupo_alimenticio": trait_by_taxon[taxon]["grupo_resumido"],
            "grupo_alimenticio_fuente": trait_by_taxon[taxon]["grupo_alimenticio"],
            "clase_cp": trait_by_taxon[taxon]["clase_cp"],
            "clase_pp": trait_by_taxon[taxon]["clase_pp"],
            "masa_ug": trait_by_taxon[taxon]["masa_ug"],
            "parcelas_con_presencia": sum(value > 0 for value in values),
            "parcelas_totales": len(values),
            "abundancia_total": sum(values),
            "abundancia_media_por_parcela": sum(values) / len(values),
            "conteos_no_reportados_tratados_como_cero_en_fuente": nonreported,
        })
    taxon_summary_rows.sort(key=lambda row: (-float(row["abundancia_total"]), str(row["taxon"])))
    for rank, row in enumerate(taxon_summary_rows, start=1):
        row["rango_abundancia_total"] = rank

    by_farm: dict[int, dict[str, str]] = defaultdict(dict)
    for parcel, meta in parcel_meta.items():
        by_farm[int(meta["finca_id"])][str(meta["tratamiento"])] = parcel
    comparison_rows: list[dict[str, object]] = []
    comparison_families = {
        "indicadores", "indices_ninja", "huellas_ninja", "porcentajes_ninja", "grupos_composicion"
    }
    public_lookup = {
        (str(row["parcela"]), str(row["familia"]), str(row["variable"])): row
        for row in public_rows
    }
    variables = sorted({
        (str(row["familia"]), str(row["variable"]), str(row["etiqueta"]), str(row["unidad"]))
        for row in public_rows if row["familia"] in comparison_families
    })
    for farm, treatments in sorted(by_farm.items()):
        if set(treatments) != {"Pina", "Bosque"}:
            continue
        for family, variable, label, unit in variables:
            pina = public_lookup[(treatments["Pina"], family, variable)]
            forest = public_lookup[(treatments["Bosque"], family, variable)]
            pina_value = float(pina["valor"])
            forest_value = float(forest["valor"])
            comparison_rows.append({
                "finca_id": farm, "familia": family, "variable": variable,
                "etiqueta": label, "unidad": unit,
                "parcela_pina": treatments["Pina"], "valor_pina": pina_value,
                "parcela_bosque": treatments["Bosque"], "valor_bosque": forest_value,
                "diferencia_pina_menos_bosque": pina_value - forest_value,
            })

    summary_columns = IDENTITY + ["abundancia_total", "riqueza_taxones", *NINJA_VARIABLES]
    group_columns = IDENTITY + ["grupo_alimenticio", "abundancia_absoluta", "porcentaje_abundancia"]
    taxon_columns = [
        "rango_abundancia_total", "taxon", "grupo_alimenticio", "grupo_alimenticio_fuente",
        "clase_cp", "clase_pp", "masa_ug", "parcelas_con_presencia",
        "parcelas_totales", "abundancia_total", "abundancia_media_por_parcela",
        "conteos_no_reportados_tratados_como_cero_en_fuente",
    ]
    comparison_columns = [
        "finca_id", "familia", "variable", "etiqueta", "unidad", "parcela_pina",
        "valor_pina", "parcela_bosque", "valor_bosque", "diferencia_pina_menos_bosque",
    ]
    public_columns = IDENTITY + ["familia", "variable", "etiqueta", "unidad", "valor", "estado", "detalle"]
    trait_public_columns = [
        "taxon", "grupo_alimenticio", "grupo_resumido", "clase_cp", "clase_pp", "masa_ug"
    ]
    trait_public_rows = [
        {
            "taxon": taxon,
            "grupo_alimenticio": trait_by_taxon[taxon]["grupo_alimenticio"],
            "grupo_resumido": trait_by_taxon[taxon]["grupo_resumido"],
            "clase_cp": trait_by_taxon[taxon]["clase_cp"],
            "clase_pp": trait_by_taxon[taxon]["clase_pp"],
            "masa_ug": trait_by_taxon[taxon]["masa_ug"],
        }
        for taxon in sorted(trait_by_taxon)
    ]

    write_csv(SUMMARY / "resumen_por_parcela.csv", summary_columns, summary_rows)
    write_csv(SUMMARY / "grupos_funcionales_por_parcela.csv", group_columns, group_rows)
    write_csv(SUMMARY / "resumen_taxones.csv", taxon_columns, taxon_summary_rows)
    write_csv(SUMMARY / "comparaciones_pina_bosque.csv", comparison_columns, comparison_rows)
    write_csv(WEB / "resultados_nematodos.csv", public_columns, public_rows)
    write_csv(WEB / "rasgos_taxones.csv", trait_public_columns, trait_public_rows)
    print(f"Resumen por parcela: {len(summary_rows)} filas")
    print(f"Grupos funcionales: {len(group_rows)} filas")
    print(f"Resumen de taxones: {len(taxon_summary_rows)} filas")
    print(f"Comparaciones dentro de finca: {len(comparison_rows)} filas")
    print(f"Salida pública: {WEB / 'resultados_nematodos.csv'} ({len(public_rows)} filas)")
    print(f"Catálogo público: {WEB / 'rasgos_taxones.csv'} ({len(trait_public_rows)} filas)")


if __name__ == "__main__":
    main()
