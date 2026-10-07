"""Genera el análisis descriptivo y la salida web de carbono lábil (POXC).

Lee exclusivamente la tabla validada por 07_prepare_poxc_data.py. Resume los
tratamientos y calcula diferencias Piña menos Bosque solo dentro de las fincas
que contienen ambos usos. No realiza pruebas inferenciales ni crea repeticiones
R: el informe fuente publica un único resultado final por parcela.
"""
from __future__ import annotations

import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "processed" / "poxc_analisis_listo" / "resultados_poxc.csv"
OUT = INPUT.parent
SUMMARY = OUT / "resumenes"
WEB = OUT / "web"

VARIABLE = "poxc"
LABEL = "Carbono lábil (POXC)"
UNIT = "mg POXC/kg de suelo seco"
REQUIRED_COLUMNS = {
    "linea_informe", "codigo_muestra", "descripcion_informe", "finca_id", "tratamiento",
    "lote", "parcela", "productor_finca", "variable", "etiqueta", "unidad",
    "resultado_original", "valor", "operador", "limite_reportado", "estado",
    "archivo_origen", "pagina_origen", "sha256_origen",
}
PUBLIC_COLUMNS = [
    "parcela", "tratamiento", "lote", "finca_id", "productor_finca", "variable",
    "unidad", "resultado_original", "valor", "operador", "limite_reportado", "estado",
]


def clean_text(value: object) -> str:
    return "" if value is None else " ".join(str(value).split())


def positive_integer(value: object, context: str) -> int:
    text = clean_text(value)
    if not text.isdigit() or int(text) <= 0:
        raise ValueError(f"{context}: se esperaba un entero positivo y se encontró {value!r}.")
    return int(text)


def finite_number(value: object, context: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{context}: resultado no numérico {value!r}.") from error
    if not math.isfinite(result):
        raise ValueError(f"{context}: resultado no finito {value!r}.")
    return result


def read_records() -> list[dict[str, object]]:
    if not INPUT.exists():
        raise FileNotFoundError(f"No existe {INPUT}. Ejecuta primero python src/07_prepare_poxc_data.py.")
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    if not REQUIRED_COLUMNS.issubset(fields):
        missing = sorted(REQUIRED_COLUMNS - fields)
        raise ValueError(f"{INPUT.name}: faltan columnas requeridas: {missing}.")
    if len(rows) != 12:
        raise ValueError(f"{INPUT.name}: se esperaban 12 resultados y se encontraron {len(rows)}.")

    seen_lines: set[int] = set()
    seen_codes: set[str] = set()
    seen_parcels: set[str] = set()
    normalized: list[dict[str, object]] = []
    for row in rows:
        line = positive_integer(row["linea_informe"], "Línea del informe")
        code = clean_text(row["codigo_muestra"])
        farm = positive_integer(row["finca_id"], f"Finca de {code}")
        lot = positive_integer(row["lote"], f"Lote de {code}")
        treatment = clean_text(row["tratamiento"])
        parcel = clean_text(row["parcela"])
        value = finite_number(row["valor"], f"POXC de {code}")
        original = finite_number(row["resultado_original"], f"Resultado original de {code}")
        if line in seen_lines or code in seen_codes or parcel in seen_parcels:
            raise ValueError(f"Resultado duplicado en la entrada: línea {line}, {code}, {parcel}.")
        if treatment not in {"Pina", "Bosque"} or parcel != f"{treatment}_{lot}":
            raise ValueError(f"Identificación de parcela inválida para {code}: {parcel}.")
        if row["variable"] != VARIABLE or row["etiqueta"] != LABEL or row["unidad"] != UNIT:
            raise ValueError(f"Definición de POXC discordante para {code}.")
        if row["estado"] != "cuantificado" or row["operador"] != "=" or row["limite_reportado"] != "":
            raise ValueError(f"Estado de resultado inesperado para {code}.")
        if value <= 0 or not math.isclose(value, original, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"Valor y resultado original incompatibles para {code}.")
        if not clean_text(row["archivo_origen"]) or positive_integer(row["pagina_origen"], f"Página de {code}") != 1:
            raise ValueError(f"Procedencia incompleta para {code}.")
        digest = clean_text(row["sha256_origen"])
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest.lower()):
            raise ValueError(f"SHA-256 inválido para {code}.")
        seen_lines.add(line)
        seen_codes.add(code)
        seen_parcels.add(parcel)
        normalized.append({**row, "linea_informe": line, "finca_id": farm, "lote": lot, "valor": value})

    if seen_lines != set(range(1, 13)):
        raise ValueError(f"Las líneas del informe no corresponden al intervalo 1–12: {sorted(seen_lines)}.")
    treatments = Counter(str(row["tratamiento"]) for row in normalized)
    if treatments != Counter({"Pina": 8, "Bosque": 4}):
        raise ValueError(f"Cobertura inesperada por tratamiento: {dict(treatments)}.")
    if len({str(row["sha256_origen"]) for row in normalized}) != 1:
        raise ValueError("Los resultados no comparten la misma huella del PDF de origen.")
    return normalized


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]], *, web: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8" if web else "utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def analyze(records: list[dict[str, object]]) -> dict[str, tuple[list[str], list[dict[str, object]], bool]]:
    by_treatment: dict[str, list[float]] = defaultdict(list)
    by_farm: dict[int, dict[str, dict[str, object]]] = defaultdict(dict)
    for record in records:
        treatment = str(record["tratamiento"])
        by_treatment[treatment].append(float(record["valor"]))
        farm = int(record["finca_id"])
        if treatment in by_farm[farm]:
            raise ValueError(f"Más de una parcela {treatment} en la Finca {farm}.")
        by_farm[farm][treatment] = record

    summary_rows: list[dict[str, object]] = []
    for treatment in ("Pina", "Bosque"):
        values = sorted(by_treatment[treatment])
        summary_rows.append({
            "tratamiento": treatment,
            "n_parcelas": len(values),
            "media": statistics.fmean(values),
            "mediana": statistics.median(values),
            "minimo": min(values),
            "maximo": max(values),
            "unidad": UNIT,
        })

    comparison_rows: list[dict[str, object]] = []
    for farm, treatments in sorted(by_farm.items()):
        if "Bosque" not in treatments:
            continue
        if "Pina" not in treatments:
            raise ValueError(f"La Finca {farm} tiene Bosque, pero no una parcela de Piña para comparar.")
        pina = treatments["Pina"]
        forest = treatments["Bosque"]
        pina_value = float(pina["valor"])
        forest_value = float(forest["valor"])
        comparison_rows.append({
            "finca_id": farm,
            "productor_finca": pina["productor_finca"],
            "parcela_pina": pina["parcela"],
            "poxc_pina": pina_value,
            "parcela_bosque": forest["parcela"],
            "poxc_bosque": forest_value,
            "diferencia_pina_menos_bosque": pina_value - forest_value,
            "unidad": UNIT,
        })
    if len(comparison_rows) != 4:
        raise ValueError(f"Se esperaban 4 comparaciones Piña–Bosque y se encontraron {len(comparison_rows)}.")

    public_rows = [{column: record[column] for column in PUBLIC_COLUMNS} for record in records]
    return {
        "resumenes/resumen_por_tratamiento.csv": (
            ["tratamiento", "n_parcelas", "media", "mediana", "minimo", "maximo", "unidad"],
            summary_rows,
            False,
        ),
        "resumenes/comparaciones_pina_bosque.csv": (
            [
                "finca_id", "productor_finca", "parcela_pina", "poxc_pina", "parcela_bosque",
                "poxc_bosque", "diferencia_pina_menos_bosque", "unidad",
            ],
            comparison_rows,
            False,
        ),
        "web/resultados_poxc.csv": (PUBLIC_COLUMNS, public_rows, True),
    }


def main() -> None:
    outputs = analyze(read_records())
    for relative_path, (columns, rows, is_web) in outputs.items():
        path = OUT / relative_path
        write_csv(path, columns, rows, web=is_web)
        print(f" - {path.relative_to(ROOT)}: {len(rows)} filas")


if __name__ == "__main__":
    main()
