"""Prepara los resultados de carbono lábil (POXC) del informe LAIMEC-042-2026.

El PDF firmado es la fuente canónica. Como no contiene una tabla estructurada,
los 12 resultados publicados en su primera página se transcriben explícitamente
en este código. Antes de escribir cualquier salida se verifica la huella SHA-256
del PDF, la correspondencia con el diseño de muestreo y la integridad de todos
los valores. El triplicado descrito en el método es analítico: el informe solo
publica un resultado final por muestra y no permite reconstruir repeticiones R.
"""
from __future__ import annotations

import csv
import hashlib
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "raw" / "pina" / "PoxC"
SOURCE_PATTERN = "LAIMEC-042-2026*.pdf"
DESIGN = ROOT / "processed" / "diseno_muestreo.csv"
OUT = ROOT / "processed" / "poxc_analisis_listo"

EXPECTED_SHA256 = "b55a33273c5fd437cf3391a822aa200c1389cf3aac90a1b0f6b6c692a729336f"
REPORT_CODE = "LAIMEC-042-2026"
REPORT_DATE = "2026-08-21"
SAMPLE_RECEIPT_DATE = "2026-02-24"
PROJECT = (
    "C6-469 Salud del Suelo en cultivos de Costa Rica: interacción de la comunidad de "
    "nemátodos con indicadores biológicos, físicos y químicos"
)
VARIABLE = "poxc"
LABEL = "Carbono lábil (POXC)"
UNIT = "mg POXC/kg de suelo seco"
METHOD = (
    "Carbono oxidable por permanganato; 2,5 g de suelo seco al aire y tamizado a <2 mm, "
    "KMnO4 a 0,02 mol/L y absorbancia a 550 nm; Culman et al. (2012)"
)

# línea, código, descripción literal del informe, POXC, finca asociada, tratamiento
REPORT_RESULTS = (
    (1, "P01-ND", "Piña #1 no disturbada", 513, 1, "Bosque"),
    (2, "P01", "Piña #1", 341, 1, "Pina"),
    (3, "P02", "Piña #2 (Alonso Chacón)", 447, 2, "Pina"),
    (4, "P03", "Piña #3 Misael", 690, 3, "Pina"),
    (5, "P03-ND", "Piña #3 Misael (No Disturbado)", 490, 3, "Bosque"),
    (6, "P04-ND", "Piña #4 No Disturbada (Sergio 1)", 552, 4, "Bosque"),
    (7, "P04", "Piña #4 (Sergio 1)", 229, 4, "Pina"),
    (8, "P05-ND", "Piña #5 No disturbada (Sergio 2)", 409, 5, "Bosque"),
    (9, "P05", "Piña #5 (Sergio 2)", 331, 5, "Pina"),
    (10, "P06", "Piña #6 (Marvin Z)", 297, 6, "Pina"),
    (11, "P07", "Piña #7 (Adrián)", 218, 7, "Pina"),
    (12, "P08", "Piña #8 (Senón)", 384, 8, "Pina"),
)

def clean_text(value: object) -> str:
    return "" if value is None else re.sub(r"\s+", " ", str(value)).strip()


def ascii_text(value: object) -> str:
    return unicodedata.normalize("NFKD", clean_text(value)).encode("ascii", "ignore").decode()


def find_source() -> Path:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"No existe la carpeta de origen: {SOURCE_DIR}")
    matches = sorted(SOURCE_DIR.glob(SOURCE_PATTERN))
    if len(matches) != 1:
        names = [path.name for path in matches]
        raise FileNotFoundError(
            f"Se esperaba un único PDF {SOURCE_PATTERN!r} en {SOURCE_DIR}; encontrados: {names}."
        )
    source = matches[0]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(
            f"La huella SHA-256 de {source.name} cambió. Esperada: {EXPECTED_SHA256}; "
            f"encontrada: {digest}. Revisa el PDF y actualiza la transcripción de forma controlada."
        )
    return source


def read_design(path: Path) -> tuple[dict[tuple[int, str], dict[str, str]], dict[int, str]]:
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}. Ejecuta primero src/01_soil_data_pipeline.py.")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = set(reader.fieldnames or [])
    required = {"finca_id", "tratamiento", "lote", "parcela", "productor_ficha"}
    if not rows or not required.issubset(fields):
        raise ValueError(f"{path.name} no contiene las columnas requeridas: {sorted(required)}.")

    design: dict[tuple[int, str], dict[str, str]] = {}
    producers: dict[int, str] = {}
    for row in rows:
        try:
            farm = int(clean_text(row["finca_id"]))
            lot = int(clean_text(row["lote"]))
        except ValueError as error:
            raise ValueError(f"Identificador no entero en {path.name}: {row}.") from error
        treatment = clean_text(row["tratamiento"])
        parcel = clean_text(row["parcela"])
        if treatment not in {"Pina", "Bosque"} or parcel != f"{treatment}_{lot}":
            raise ValueError(f"Fila de diseño inválida: {row}.")
        key = (farm, treatment)
        if key in design:
            raise ValueError(f"Diseño duplicado para Finca {farm}, {treatment}.")
        design[key] = row
        producer = clean_text(row["productor_ficha"])
        if producer:
            previous = producers.setdefault(farm, producer)
            if previous != producer:
                raise ValueError(f"La Finca {farm} tiene productores distintos en el diseño.")
    return design, producers


def validate_transcription() -> None:
    lines = [row[0] for row in REPORT_RESULTS]
    codes = [row[1] for row in REPORT_RESULTS]
    if lines != list(range(1, 13)) or len(set(codes)) != 12:
        raise ValueError("La transcripción debe contener las líneas 1 a 12 y códigos únicos.")
    treatments = Counter(row[5] for row in REPORT_RESULTS)
    if treatments != Counter({"Pina": 8, "Bosque": 4}):
        raise ValueError(f"Distribución de tratamientos inesperada: {dict(treatments)}.")
    for line, code, description, value, farm, treatment in REPORT_RESULTS:
        match = re.fullmatch(r"P(\d{2})(-ND)?", code)
        if not match or int(match.group(1)) != farm:
            raise ValueError(f"Línea {line}: código y finca discordantes: {code}, Finca {farm}.")
        is_nd = match.group(2) is not None
        if is_nd != (treatment == "Bosque"):
            raise ValueError(f"Línea {line}: el sufijo ND no coincide con {treatment}.")
        if is_nd and "disturb" not in ascii_text(description).lower():
            raise ValueError(f"Línea {line}: la descripción ND no indica condición no disturbada.")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Línea {line}: resultado POXC no numérico: {value!r}.")
        if not math.isfinite(float(value)) or value <= 0:
            raise ValueError(f"Línea {line}: resultado POXC no positivo: {value!r}.")


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def prepare() -> dict[str, tuple[list[str], list[dict[str, object]]]]:
    source = find_source()
    validate_transcription()
    design, producers = read_design(DESIGN)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    source_relative = source.relative_to(ROOT).as_posix()

    records: list[dict[str, object]] = []
    parcels: set[str] = set()
    for line, code, description, value, farm, treatment in REPORT_RESULTS:
        key = (farm, treatment)
        if key not in design:
            raise ValueError(f"{code} no tiene correspondencia para Finca {farm}, {treatment}.")
        design_row = design[key]
        lot = int(design_row["lote"])
        parcel = clean_text(design_row["parcela"])
        if parcel in parcels:
            raise ValueError(f"Más de un resultado POXC fue asignado a {parcel}.")
        parcels.add(parcel)
        record = {
            "linea_informe": line,
            "codigo_muestra": code,
            "descripcion_informe": description,
            "finca_id": farm,
            "tratamiento": treatment,
            "lote": lot,
            "parcela": parcel,
            "productor_finca": producers.get(farm, ""),
            "variable": VARIABLE,
            "etiqueta": LABEL,
            "unidad": UNIT,
            "resultado_original": value,
            "valor": value,
            "operador": "=",
            "limite_reportado": "",
            "estado": "cuantificado",
            "fecha_recepcion_muestras": SAMPLE_RECEIPT_DATE,
            "fecha_informe": REPORT_DATE,
            "codigo_informe": REPORT_CODE,
            "proyecto": PROJECT,
            "metodo": METHOD,
            "archivo_origen": source_relative,
            "pagina_origen": 1,
            "sha256_origen": digest,
            "criterio_correspondencia": (
                "Código Pxx vinculado con Piña de la misma finca; Pxx-ND vinculado con Bosque "
                "de la misma finca según diseno_muestreo.csv"
            ),
        }
        records.append(record)

    if len(parcels) != 12:
        raise ValueError(f"Se esperaban 12 parcelas únicas y se encontraron {len(parcels)}.")

    audit = [
        {"control": "archivo_origen", "resultado": source.name, "detalle": "PDF firmado preservado sin cambios"},
        {"control": "sha256_origen", "resultado": digest, "detalle": "Coincide con la huella esperada por el código"},
        {"control": "codigo_informe", "resultado": REPORT_CODE, "detalle": f"Fecha {REPORT_DATE}"},
        {"control": "resultados_transcritos", "resultado": len(records), "detalle": "Tabla de la página 1 del PDF"},
        {"control": "parcelas", "resultado": len(parcels), "detalle": "8 Piña y 4 Bosque"},
        {"control": "variable", "resultado": VARIABLE, "detalle": f"{LABEL}; {UNIT}"},
        {"control": "correspondencia_nd", "resultado": "Bosque", "detalle": "Pxx-ND se asocia al Bosque de la misma finca"},
        {"control": "triplicado_analitico", "resultado": "sin valores individuales", "detalle": "El PDF publica un resultado final por muestra; no se crean repeticiones R"},
    ]

    full_columns = [
        "linea_informe", "codigo_muestra", "descripcion_informe", "finca_id", "tratamiento",
        "lote", "parcela", "productor_finca", "variable", "etiqueta", "unidad",
        "resultado_original", "valor", "operador", "limite_reportado", "estado",
        "fecha_recepcion_muestras", "fecha_informe", "codigo_informe", "proyecto", "metodo",
        "archivo_origen", "pagina_origen", "sha256_origen", "criterio_correspondencia",
    ]
    return {
        "resultados_poxc.csv": (full_columns, records),
        "auditoria_preparacion.csv": (["control", "resultado", "detalle"], audit),
    }


def main() -> None:
    outputs = prepare()
    for relative_path, (columns, rows) in outputs.items():
        path = OUT / relative_path
        write_csv(path, columns, rows)
        print(f" - {path.relative_to(ROOT)}: {len(rows)} filas")


if __name__ == "__main__":
    main()
