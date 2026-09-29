from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path

import pandas as pd

# Orden de ejecucion: 01
# Procesa el archivo físico ordenado y deja la salida lista para análisis.

PHYSICAL_SHEETS = {
    'densidad_porosidad': [
        'ID USUARIO',
        'ID LAB',
        'Densidad aparente (g cm-3)',
        'Densidad Particulas (g cm-3)',
        'Porosidad (%)',
        'xls_origen',
    ],
    'textural': [
        'ID USUARIO',
        'ID LAB',
        'ARENA (%)',
        'LIMO (%)',
        'ARCILLA (%)',
        'Clase textural (%)',
        'Estabilidad de agregados (%)',
        'xls_origen',
    ],
    'retencion_humedad': [
        'ID USUARIO',
        'ID LAB',
        'Humedad gravimétrica (%) (0,33 bar)',
        'Humedad gravimétrica (%) (15 bar)',
        'Agua útil (%)',
        'xls_origen',
    ],
}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ''
    text = str(value).strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace('ñ', 'n').replace('Ñ', 'N')
    text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
    text = text.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
    text = text.replace('%', ' ')
    text = re.sub(r'[^A-Za-z0-9\s_-]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def normalize_column_name(value: object) -> str:
    text = normalize_text(value)
    text = text.lower()
    text = text.replace('-', '_')
    text = re.sub(r'[^a-z0-9_\s]+', '', text)
    text = re.sub(r'\s+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text


def parse_numeric(value: object):
    if pd.isna(value):
        return None
    text = str(value).strip().replace(' ', '')
    if text in {'', 'nan', 'NaN', 'na', 'N/A'}:
        return None
    text = text.replace('%', '')
    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return None


def clean_value(value: object):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if value == '':
        return None
    if value.lower() in {'nan', 'na', 'n/a'}:
        return None

    num = parse_numeric(value)
    if num is not None:
        return num

    norm = normalize_text(value)
    if norm == '':
        return None
    return norm


def normalize_id_usuario(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('PIÑA', 'Pina').replace('PINA', 'Pina')
    return text.strip()


def parse_id_usuario(value: object) -> dict[str, str]:
    text = normalize_id_usuario(value)
    result = dict.fromkeys(
        ['id_usuario_normalizado', 'zona', 'tratamiento', 'lote', 'repeticion', 'productor'], ''
    )
    result['id_usuario_normalizado'] = text
    match = re.match(r'^(Pina|Bosque)\s*(\d+)\b(.*)$', text, flags=re.I)
    if not match:
        return result

    zona = 'Bosque' if match[1].lower() == 'bosque' else 'Pina'
    lote = str(int(match[2]))
    tail = match[3].strip()
    # El sufijo de Piña 1-1 es una submuestra, no el nombre del productor.
    short = re.fullmatch(r'-\s*(\d+)', tail)
    explicit = re.search(r'\bR\s*(\d+)\s*$', tail, flags=re.I)
    repeticion = str(int((short or explicit)[1])) if (short or explicit) else ''
    productor = '' if short else (tail[:explicit.start()] if explicit else tail).strip(' -')
    normalized = f'{zona} {lote}'
    if productor:
        normalized += f' {productor}'
    if repeticion:
        normalized += f' R{repeticion}'
    result.update(id_usuario_normalizado=normalized, zona=zona, tratamiento=zona,
                  lote=lote, repeticion=repeticion, productor=productor)
    return result


def select_relevant_columns(df: pd.DataFrame, want_columns: list[str]) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    column_map = {normalize_column_name(col): col for col in df.columns if pd.notna(col)}
    selected = []
    for expected in want_columns:
        key = normalize_column_name(expected)
        if key in column_map:
            selected.append(column_map[key])

    if not selected:
        return pd.DataFrame(columns=[normalize_column_name(c) for c in want_columns])

    return df.loc[:, selected].copy()


def build_analysis_table(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    if df.empty:
        raise ValueError(f'La hoja {sheet_name} no contiene resultados.')

    expected = {normalize_column_name(col) for col in PHYSICAL_SHEETS[sheet_name]}
    found = [normalize_column_name(col) for col in df.columns]
    if expected - set(found):
        raise ValueError(f'Faltan columnas en {sheet_name}: {sorted(expected - set(found))}')
    if any(found.count(col) != 1 for col in expected):
        raise ValueError(f'Hay encabezados duplicados en {sheet_name}.')

    selected = select_relevant_columns(df, PHYSICAL_SHEETS[sheet_name])
    selected = selected.dropna(how='all').reset_index(drop=True)
    if selected.empty:
        return selected

    selected.columns = [normalize_column_name(col) for col in selected.columns]

    if 'id_usuario' in selected.columns:
        selected['id_usuario'] = selected['id_usuario'].apply(normalize_id_usuario)
        parsed = selected['id_usuario'].apply(parse_id_usuario)
        parsed_df = pd.DataFrame(list(parsed))
        selected = pd.concat([selected, parsed_df], axis=1)

    for col in selected.columns:
        if col in {'id_usuario', 'id_lab', 'xls_origen', 'id_usuario_normalizado', 'zona', 'tratamiento', 'lote', 'repeticion', 'productor'}:
            if col == 'id_usuario':
                continue
            selected[col] = selected[col].apply(lambda x: normalize_text(x) if pd.notna(x) else None)
        else:
            if col == 'clase_textural':
                selected[col] = selected[col].apply(clean_value)
                continue
            def numeric_result(value):
                if pd.isna(value) or str(value).strip().lower() in {'', 'nan', 'na', 'n/a'}:
                    return None
                number = parse_numeric(value)
                if number is None or not math.isfinite(number):
                    raise ValueError(f'Resultado numérico inválido en {sheet_name}/{col}: {value!r}')
                return number
            selected[col] = selected[col].apply(numeric_result)

    return selected


def read_field_design(source: Path) -> pd.DataFrame:
    """Lee solo la correspondencia agronómica, sin datos de contacto personales."""
    raw = pd.read_excel(source, header=None)
    header_rows = [i for i, row in raw.iterrows()
                   if {'finca', 'zona_con_cultivo', 'zona_no_disturbada'}.issubset(
                       {normalize_column_name(v) for v in row})]
    if len(header_rows) != 1:
        raise ValueError(f'No se identifica una cabecera única de fincas en {source}')
    header = header_rows[0]
    frame = raw.iloc[header + 1:].copy()
    frame.columns = [normalize_column_name(v) for v in raw.iloc[header]]
    records = []
    for _, row in frame.dropna(subset=['finca']).iterrows():
        finca = parse_numeric(row['finca'])
        if finca is None or not math.isfinite(finca) or finca <= 0 or not finca.is_integer():
            raise ValueError(f'Identificador de finca inválido: {row["finca"]!r}')
        productor_finca = normalize_text(row['productor'])
        for field in ['zona_con_cultivo', 'zona_no_disturbada']:
            if pd.isna(row[field]):
                continue
            parsed = parse_id_usuario(row[field])
            if not parsed['tratamiento'] or not parsed['lote']:
                raise ValueError(f'Parcela no reconocida en la ficha: {row[field]}')
            record = {
                'finca_id': int(finca),
                'tratamiento': parsed['tratamiento'],
                'lote': parsed['lote'],
                'parcela': f"{parsed['tratamiento']}_{parsed['lote']}",
                'productor_ficha': productor_finca if field == 'zona_con_cultivo' else '',
                'fecha_ficha': pd.to_datetime(row['fecha']).strftime('%Y-%m-%d'),
                'fuente_diseno': source.name,
            }
            records.append(record)
    design = pd.DataFrame(records)
    if design.duplicated(['tratamiento', 'lote']).any():
        raise ValueError('Una parcela aparece asignada a más de una finca en la ficha.')
    return design


def consolidate_lab_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Consolida copias idénticas por ID LAB; los resultados discordantes son errores."""
    if df['id_lab'].isna().any() or df['id_lab'].eq('').any():
        raise ValueError('Hay muestras sin ID LAB; no se pueden consolidar de forma segura.')
    duplicates = df.loc[df.duplicated('id_lab', keep=False)].copy()
    compare = [c for c in df if c not in {'id_lab', 'xls_origen', 'id_usuario'}]
    for lab_id, group in duplicates.groupby('id_lab'):
        if len(group[compare].drop_duplicates()) != 1:
            raise ValueError(f'Resultados discordantes para {lab_id}; revisar antes de analizar.')
    unique = df.drop_duplicates('id_lab').copy()
    origins = df.groupby('id_lab')['xls_origen'].agg(
        lambda values: ' | '.join(sorted(set(values.dropna().astype(str))))
    )
    unique['xls_origen'] = unique['id_lab'].map(origins)
    return unique.reset_index(drop=True), duplicates


def export_analysis_ready(project_root: Path) -> dict[str, Path]:
    source = project_root / 'processed' / 'fisico_all_pina' / 'Fisico_all_sorted.xlsx'
    if not source.exists():
        raise FileNotFoundError(f'No existe el archivo físico ordenado: {source}')

    output_dir = project_root / 'processed' / 'analisis_listo'
    output_dir.mkdir(parents=True, exist_ok=True)

    design_source = project_root / 'raw' / 'pina' / 'PIÑA FINCAS PRODUCTORAS .xlsx'
    design = read_field_design(design_source)
    farm_names = design.loc[design['productor_ficha'].fillna('').ne(''),
                            ['finca_id', 'productor_ficha']].drop_duplicates()
    if farm_names.duplicated('finca_id').any():
        raise ValueError('Hay nombres de productor distintos para la misma finca en la ficha.')
    producer_by_farm = farm_names.set_index('finca_id')['productor_ficha'].to_dict()
    xls = pd.ExcelFile(source)
    exported = {}
    prepared = {}
    audit = []
    duplicate_records = []
    for sheet_name in ['densidad_porosidad', 'textural', 'retencion_humedad']:
        if sheet_name not in xls.sheet_names:
            raise ValueError(f'Falta la hoja requerida: {sheet_name}')
        df = pd.read_excel(source, sheet_name=sheet_name, header=0)
        cleaned = build_analysis_table(df, sheet_name)
        input_rows = len(cleaned)
        missing_reps_before = int(cleaned['id_usuario'].str.contains(r'-\s*\d+\s*$', regex=True).sum())
        cleaned, duplicates = consolidate_lab_duplicates(cleaned)
        duplicates.insert(0, 'tabla', sheet_name)
        duplicate_records.append(duplicates)
        cleaned = cleaned.merge(design, on=['tratamiento', 'lote'], how='left',
                                validate='many_to_one', indicator=True)
        if not cleaned['_merge'].eq('both').all():
            raise ValueError(f'Hay parcelas de {sheet_name} sin correspondencia en la ficha de fincas.')
        cleaned = cleaned.drop(columns='_merge')
        if cleaned['repeticion'].eq('').any():
            raise ValueError(f'Hay submuestras sin identificar en {sheet_name}.')
        if cleaned.duplicated(['parcela', 'repeticion']).any():
            raise ValueError(f'Hay varios ID LAB para la misma submuestra en {sheet_name}.')
        audit.append({'tabla': sheet_name, 'filas_entrada': input_rows,
                      'muestras_unicas': len(cleaned),
                      'copias_consolidadas': input_rows - len(cleaned),
                      'submuestras_formato_guion': missing_reps_before})
        prepared[sheet_name] = cleaned

    # Validar todas las tablas antes de sustituir las salidas generadas.
    dashboard_columns = {
        'densidad_porosidad': [
            'densidad_aparente_g_cm_3', 'densidad_particulas_g_cm_3', 'porosidad',
        ],
        'textural': ['arena', 'limo', 'arcilla', 'estabilidad_de_agregados'],
        'retencion_humedad': [
            'humedad_gravimetrica_0_33_bar', 'humedad_gravimetrica_15_bar', 'agua_util',
        ],
    }
    dashboard_dir = output_dir / 'web'
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    for sheet_name, cleaned in prepared.items():
        out_path = output_dir / f'{sheet_name}.csv'
        cleaned.to_csv(out_path, index=False)
        exported[sheet_name] = out_path
        public_columns = ['tratamiento', 'finca_id', 'lote', 'repeticion', 'parcela'] + dashboard_columns[sheet_name]
        public = cleaned.loc[:, public_columns].copy()
        public['productor_finca'] = cleaned['finca_id'].map(producer_by_farm).fillna('')
        public.to_csv(
            dashboard_dir / out_path.name, index=False, encoding='utf-8'
        )
    design.to_csv(project_root / 'processed' / 'diseno_muestreo.csv', index=False)
    pd.DataFrame(audit).to_csv(project_root / 'processed' / 'auditoria_preparacion.csv', index=False)
    pd.concat(duplicate_records, ignore_index=True).to_csv(
        project_root / 'processed' / 'duplicados_consolidados.csv', index=False)
    return exported


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    exported = export_analysis_ready(project_root)
    print('Salida lista para análisis:')
    for sheet_name, path in exported.items():
        print(f' - {sheet_name}: {path.name}')


if __name__ == '__main__':
    main()
