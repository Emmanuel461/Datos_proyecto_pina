"""Prepara el reporte químico preservando resultados censurados y su procedencia."""
from pathlib import Path
import math
import re

import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'processed/quimico_all_pina/quimico_all.xlsx'
OUT = ROOT / 'processed/quimico_analisis_listo'
VARIABLES = [
    ('ph', 'H₂O', 'adimensional'), ('acidez', 'Acidez', 'cmol(+)/L'),
    ('ca', 'Ca', 'cmol(+)/L'), ('mg', 'Mg', 'cmol(+)/L'),
    ('k', 'K', 'cmol(+)/L'), ('cice', 'CICE', 'cmol(+)/L'),
    ('sa', 'SA', '%'), ('p', 'P', 'mg/L'), ('zn', 'Zn', 'mg/L'),
    ('cu', 'Cu', 'mg/L'), ('fe', 'Fe', 'mg/L'), ('mn', 'Mn', 'mg/L'),
    ('ce', 'CE', 'mS/cm'), ('c', 'C', '%'), ('n', 'N', '%'),
    ('c_n', 'C/N', 'adimensional'),
]


def parse_result(value):
    """Un límite nunca se almacena como una concentración medida."""
    if value is None or str(value).strip() == '':
        return None, '', None, 'faltante'
    match = re.fullmatch(r'\s*(<=|>=|<|>|≤|≥)?\s*([+-]?\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?)\s*', str(value))
    if not match:
        raise ValueError(f'Resultado no reconocido: {value!r}')
    operator = (match[1] or '=').replace('≤', '<=').replace('≥', '>=')
    number = float(match[2].replace(',', '.'))
    if not math.isfinite(number) or number < 0:
        raise ValueError(f'Resultado inválido: {value!r}')
    if operator == '=':
        return number, operator, None, 'cuantificado'
    return None, operator, number, 'censurado'


def main():
    book = load_workbook(SOURCE, data_only=True, read_only=True)
    sheet = book.worksheets[0]
    # Validar el formato evita leer niveles críticos como observaciones.
    assert sheet['A18'].value == 'ID USUARIO' and sheet['D18'].value == 'ID LAB'
    for col, (_, header, _) in enumerate(VARIABLES, 5):
        if sheet.cell(17, col).value != header:
            raise ValueError(f'Encabezado inesperado en columna {col}')
    records = []
    for row in sheet.iter_rows(min_row=19):
        user_id, lab_id = row[0].value, row[3].value
        if not re.fullmatch(r'S-\d{2}-\d+', str(lab_id)):
            continue
        match = re.fullmatch(r'(PIÑA|BOSQUE)\s+(\d+)\s*(?:\(.*\))?', str(user_id))
        if not match:
            raise ValueError(f'Parcela no reconocida: {user_id}')
        treatment = 'Pina' if match[1] == 'PIÑA' else 'Bosque'
        for col, (variable, _, unit) in enumerate(VARIABLES, 4):
            cell = row[col]
            number, operator, limit, state = parse_result(cell.value)
            records.append(dict(
                parcela=f'{treatment}_{match[2]}', tratamiento=treatment,
                lote=int(match[2]), id_usuario_original=user_id, id_lab=lab_id,
                variable=variable, unidad=unit, resultado_original=cell.value,
                valor=number, operador=operator, limite_reportado=limit,
                estado=state, archivo=SOURCE.relative_to(ROOT).as_posix(),
                hoja=sheet.title, celda=cell.coordinate,
            ))
    book.close()
    df = pd.DataFrame(records)
    if df.empty or df.duplicated(['parcela', 'variable']).any() or df.duplicated(['id_lab', 'variable']).any():
        raise ValueError('No hay resultados o existen muestras duplicadas')
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / 'resultados_quimicos.csv', index=False, encoding='utf-8-sig')
    df[df.estado != 'cuantificado'].to_csv(OUT / 'resultados_no_cuantificados.csv', index=False, encoding='utf-8-sig')
    # Vista legible: conserva literalmente <1; para calcular usar el archivo largo.
    df.pivot(index=['parcela', 'id_lab'], columns='variable', values='resultado_original').to_csv(
        OUT / 'quimica_por_parcela.csv', encoding='utf-8-sig')
    print(f'{df.parcela.nunique()} parcelas, {len(df)} resultados, '
          f'{sum(df.estado == "censurado")} censurados, {sum(df.estado == "faltante")} faltantes.')


if __name__ == '__main__':
    main()
