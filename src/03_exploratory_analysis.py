from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

# Parcela = tratamiento × lote; R = submuestra, según el responsable del estudio.
ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = ROOT / 'processed' / 'analisis_listo'
SUMMARY_DIR = ANALYSIS_DIR / 'resumenes'
DOCS_DIR = ROOT / 'docs'
COLORS = {'Pina': '#bf801a', 'Bosque': '#24745b'}
NAMES = {'Pina': 'Piña', 'Bosque': 'Bosque'}
CHARACTERIZATION_ORDER = ['Bosque', 'Pina']
VARIABLES = {
    'densidad_porosidad': {
        'densidad_aparente_g_cm_3': ('Densidad aparente', 'g/cm³'),
        'densidad_particulas_g_cm_3': ('Densidad de partículas', 'g/cm³'),
        'porosidad': ('Porosidad', '%'),
    },
    'retencion_humedad': {
        'humedad_gravimetrica_0_33_bar': ('Humedad gravimétrica a 0,33 bar', '%'),
        'humedad_gravimetrica_15_bar': ('Humedad gravimétrica a 15 bar', '%'),
        'agua_util': ('Agua útil gravimétrica', '%'),
    },
    'textural': {
        'arena': ('Arena', '%'), 'limo': ('Limo', '%'), 'arcilla': ('Arcilla', '%'),
        'estabilidad_de_agregados': ('Estabilidad de agregados', '%'),
    },
}
TITLES = {'densidad_porosidad': 'Densidad y porosidad',
          'retencion_humedad': 'Retención de humedad',
          'textural': 'Textura y estabilidad de agregados'}
KEYS = ['finca_id', 'tratamiento', 'lote', 'parcela']


def load_tables(directory: Path = ANALYSIS_DIR) -> dict[str, pd.DataFrame]:
    tables = {}
    for name, variables in VARIABLES.items():
        df = pd.read_csv(directory / f'{name}.csv')
        required = set(KEYS + ['repeticion', 'id_lab', 'id_usuario', 'xls_origen']) | set(variables)
        if required - set(df):
            raise ValueError(f'{name}: faltan {sorted(required - set(df))}. Ejecutar primero 01_soil_data_pipeline.py.')
        if df[KEYS + ['repeticion', 'id_lab']].isna().any().any():
            raise ValueError(f'{name}: metadatos de muestreo incompletos.')
        for col in ['finca_id', 'lote', 'repeticion']:
            values = pd.to_numeric(df[col], errors='raise')
            if not ((values > 0) & (values % 1 == 0)).all():
                raise ValueError(f'{name}: {col} debe contener enteros positivos.')
            df[col] = values.astype(int)
        if not df['tratamiento'].isin(NAMES).all():
            raise ValueError(f'{name}: tratamiento no reconocido.')
        if df.duplicated('id_lab').any() or df.duplicated(['parcela', 'repeticion']).any():
            raise ValueError(f'{name}: muestras duplicadas; ejecutar primero la preparación.')
        if df[KEYS].drop_duplicates().duplicated('parcela').any():
            raise ValueError(f'{name}: asignaciones de parcela inconsistentes.')
        if df[KEYS].drop_duplicates().duplicated(['finca_id', 'tratamiento']).any():
            raise ValueError(f'{name}: varias parcelas por finca y tratamiento; revisar el diseño.')
        for variable in variables:
            df[variable] = pd.to_numeric(df[variable], errors='raise')
            if np.isinf(df[variable].dropna()).any():
                raise ValueError(f'{name}: valores infinitos en {variable}.')
        tables[name] = df
    return tables


def build_summaries(tables: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for name, df in tables.items():
        for key, group in df.groupby(KEYS, sort=True):
            for variable, (label, unit) in VARIABLES[name].items():
                values = group[variable].dropna()
                mean, sd = values.mean(), values.std(ddof=1)
                rows.append(dict(zip(KEYS, key)) | {
                    'tabla': name, 'variable': variable, 'indicador': label, 'unidad': unit,
                    'n_submuestras': len(group), 'n_validos': len(values),
                    'n_faltantes': int(group[variable].isna().sum()),
                    'media': mean, 'de_submuestras': sd, 'mediana': values.median(),
                    'q1': values.quantile(0.25), 'q3': values.quantile(0.75),
                    'rango_intercuartil': values.quantile(0.75) - values.quantile(0.25),
                    'minimo': values.min(), 'maximo': values.max(),
                    'amplitud': values.max() - values.min(),
                    'cv_submuestras_pct': 100 * sd / abs(mean) if pd.notna(mean) and mean != 0 else np.nan,
                })
    summary = pd.DataFrame(rows)
    # Emparejar medias por finca documentada, nunca por número de lote o R.
    join = ['tabla', 'variable', 'indicador', 'unidad', 'finca_id']
    cols = join + ['lote', 'parcela', 'media', 'n_validos']
    pina = summary.loc[summary['tratamiento'].eq('Pina'), cols]
    bosque = summary.loc[summary['tratamiento'].eq('Bosque'), cols]
    pairs = pina.merge(bosque, on=join, suffixes=('_pina', '_bosque'), validate='one_to_one')
    pairs['diferencia_pina_menos_bosque'] = pairs['media_pina'] - pairs['media_bosque']
    pairs['cambio_relativo_pct'] = 100 * pairs['diferencia_pina_menos_bosque'] / pairs['media_bosque'].replace(0, np.nan)
    pairs['unidad_diferencia'] = pairs['unidad'].replace({'%': 'puntos porcentuales'})
    return summary, pairs


def ordered_parcels(df: pd.DataFrame) -> pd.DataFrame:
    parcels = df[KEYS].drop_duplicates().copy()
    parcels['orden'] = parcels['tratamiento'].map({'Pina': 0, 'Bosque': 1})
    return parcels.sort_values(['finca_id', 'orden', 'lote']).drop(columns='orden')


def parcel_label(row, multiline: bool = False) -> str:
    sep = '\n' if multiline else ' · '
    return f'F{row.finca_id}{sep}{NAMES[row.tratamiento]} {row.lote}'


def save_figure(fig, directory: Path, name: str) -> None:
    # Sustituir el archivo completo evita abrir imágenes sincronizadas en modo lectura/escritura.
    try:
        for extension in ['png', 'svg']:
            with NamedTemporaryFile(dir=directory, suffix=f'.{extension}', delete=False) as handle:
                temporary = Path(handle.name)
            try:
                fig.savefig(temporary, dpi=180, bbox_inches='tight')
                temporary.replace(directory / f'{name}.{extension}')
            finally:
                temporary.unlink(missing_ok=True)
    finally:
        plt.close(fig)


def plot_parcel_boxplots(name: str, df: pd.DataFrame, treatment: str, out: Path) -> None:
    """Cada caja resume una parcela; cada punto identifica una submuestra real."""
    subset = df.loc[df['tratamiento'].eq(treatment)]
    if subset.empty:
        return
    parcels, variables = ordered_parcels(subset), VARIABLES[name]
    repetitions = sorted(subset['repeticion'].unique())
    palette = plt.get_cmap('tab10')
    rep_colors = {rep: palette(i % 10) for i, rep in enumerate(repetitions)}
    offsets = dict(zip(repetitions, np.linspace(-0.2, 0.2, len(repetitions))
                       if len(repetitions) > 1 else [0]))
    fig, axes = plt.subplots(len(variables), 1, figsize=(14, 3.5 * len(variables)), sharex=True)
    for ax, (variable, (label, unit)) in zip(np.atleast_1d(axes), variables.items()):
        for position, parcel in enumerate(parcels.itertuples(), start=1):
            group = subset.loc[subset['parcela'].eq(parcel.parcela)].sort_values('repeticion')
            valid = group.loc[group[variable].notna()]
            if not valid.empty:
                ax.boxplot([valid[variable].to_numpy()], positions=[position], widths=0.6,
                           whis=1.5, showfliers=False, patch_artist=True, manage_ticks=False,
                           boxprops={'facecolor': COLORS[treatment], 'alpha': 0.16},
                           medianprops={'color': '#202020', 'linewidth': 2},
                           whiskerprops={'color': '#666666'}, capprops={'color': '#666666'})
                ax.scatter(position, valid[variable].mean(), marker='D', color='black', s=30, zorder=5)
                for rep_index, (_, row) in enumerate(valid.iterrows()):
                    x = position + offsets[row['repeticion']]
                    ax.scatter(x, row[variable], color=rep_colors[row['repeticion']],
                               s=38, edgecolor='white', linewidth=0.4, zorder=6)
                    ax.annotate(f"R{int(row['repeticion'])}", (x, row[variable]),
                                xytext=(0, 6 if rep_index % 2 == 0 else -12),
                                textcoords='offset points', fontsize=7, ha='center',
                                color=rep_colors[row['repeticion']], zorder=7)
            ax.text(position, 0.98, f'n={len(valid)}', transform=ax.get_xaxis_transform(),
                    ha='center', va='top', fontsize=9, color='#555555')
        ax.set_title(label, loc='left', fontsize=12)
        ax.set_ylabel(unit)
        ax.set_xlim(0.5, len(parcels) + 0.5)
        ax.margins(y=0.22)
        ax.grid(axis='y', alpha=0.18)
    axes[-1].set_xticks(range(1, len(parcels) + 1),
                       [f'{NAMES[treatment]} {r.lote}\nFinca {r.finca_id}' for r in parcels.itertuples()])
    axes[-1].set_xlabel('Parcela')
    handles = [Line2D([], [], color=rep_colors[r], marker='o', linestyle='', label=f'R{r}') for r in repetitions]
    handles += [Line2D([], [], color='black', marker='D', linestyle='', label='Media'),
                Line2D([], [], color='#202020', linewidth=2, label='Mediana')]
    fig.suptitle(f'{NAMES[treatment]} · {TITLES[name]}\nDistribución de las submuestras dentro de cada parcela',
                 fontsize=16, y=0.995)
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.94),
               ncol=len(handles), frameon=False, fontsize=9)
    fig.text(0.5, 0.014, 'Caja: Q1–Q3 · Bigotes: observaciones hasta 1,5 × RIC desde la caja · '
             'Todos los valores se muestran como puntos', ha='center', fontsize=9, color='#444444')
    fig.tight_layout(rect=(0, 0.035, 1, 0.90))
    save_figure(fig, out, f'{name}_boxplot_{treatment.lower()}')


def plot_internal_variability(summary: pd.DataFrame, out: Path) -> None:
    """CV por parcela e indicador; una escala común y sin clasificar la calidad del suelo."""
    labels = {'densidad_aparente_g_cm_3': 'Densidad\naparente',
              'densidad_particulas_g_cm_3': 'Densidad de\npartículas', 'porosidad': 'Porosidad',
              'humedad_gravimetrica_0_33_bar': 'Humedad\n0,33 bar',
              'humedad_gravimetrica_15_bar': 'Humedad\n15 bar', 'agua_util': 'Agua útil',
              'arena': 'Arena', 'limo': 'Limo', 'arcilla': 'Arcilla',
              'estabilidad_de_agregados': 'Estabilidad de\nagregados'}
    treatments = [t for t in CHARACTERIZATION_ORDER if summary['tratamiento'].eq(t).any()]
    groups = [ordered_parcels(summary.loc[summary['tratamiento'].eq(t)]) for t in treatments]
    fig, axes = plt.subplots(len(groups), 1, figsize=(15, 3 + 0.5 * sum(map(len, groups))),
                             squeeze=False, sharex=True, layout='constrained',
                             gridspec_kw={'height_ratios': [len(g) for g in groups]})
    finite = summary['cv_submuestras_pct'].dropna()
    vmax = max(float(finite.max()), 1) if not finite.empty else 1
    cmap = plt.get_cmap('YlOrBr').copy()
    cmap.set_bad('#ededed')
    for ax, treatment, parcels in zip(axes.flat, treatments, groups):
        values = summary.loc[summary['tratamiento'].eq(treatment)].pivot(
            index='parcela', columns='variable', values='cv_submuestras_pct').reindex(
                index=parcels['parcela'], columns=list(labels)).to_numpy(dtype=float)
        im = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, aspect='auto', vmin=0, vmax=vmax)
        for (r, c), value in np.ndenumerate(values):
            ax.text(c, r, '—' if pd.isna(value) else f'{value:.1f}', ha='center', va='center',
                    fontsize=9, color='white' if pd.notna(value) and value > 0.6 * vmax else '#222222')
        ax.set_title(NAMES[treatment], loc='left', fontsize=13)
        ax.set_yticks(range(len(parcels)), [parcel_label(r) for r in parcels.itertuples()])
        ax.set_xticks(range(len(labels)), list(labels.values()), fontsize=9)
    fig.colorbar(im, ax=list(axes.flat), shrink=0.8, label='CV de submuestras (%)', pad=0.02)
    fig.suptitle('Variabilidad dentro de cada parcela\nCV = 100 × DE / |media|; cada celda resume un indicador', fontsize=15)
    save_figure(fig, out, 'variabilidad_interna_parcelas')


def textural_composition(df: pd.DataFrame) -> pd.DataFrame:
    components = ['arena', 'limo', 'arcilla']
    complete = df.dropna(subset=components)
    means = complete.groupby(KEYS)[components].mean()
    counts = complete.groupby(KEYS).size().rename('n_submuestras_completas')
    result = ordered_parcels(df).merge(pd.concat([means, counts], axis=1).reset_index(),
                                     on=KEYS, how='left', validate='one_to_one')
    result['n_submuestras_completas'] = result['n_submuestras_completas'].fillna(0).astype(int)
    return result


def plot_textural_composition(composition: pd.DataFrame, out: Path) -> None:
    treatments = [t for t in CHARACTERIZATION_ORDER if composition['tratamiento'].eq(t).any()]
    groups = [composition.loc[composition['tratamiento'].eq(t)] for t in treatments]
    fig, axes = plt.subplots(len(groups), 1, figsize=(13, 3 + 0.48 * len(composition)),
                             squeeze=False, sharex=True,
                             gridspec_kw={'height_ratios': [len(g) for g in groups]})
    components = {'arena': ('Arena', '#d6b46b'), 'limo': ('Limo', '#82b5b0'),
                  'arcilla': ('Arcilla', '#826391')}
    for ax, treatment, group in zip(axes.flat, treatments, groups):
        left = np.zeros(len(group))
        y = np.arange(len(group))
        for component, (label, color) in components.items():
            values = group[component].to_numpy(dtype=float)
            ax.barh(y, values, left=left, color=color, label=label, height=0.67,
                    edgecolor='white', linewidth=0.7)
            for pos, value in enumerate(values):
                if pd.notna(value) and value > 0:
                    ax.text(left[pos] + value / 2, pos, f'{value:.1f}', ha='center', va='center',
                            fontsize=9, color='white' if component == 'arcilla' else '#222222')
            left += np.nan_to_num(values)
        ax.set_yticks(y, [parcel_label(r) for r in group.itertuples()])
        ax.invert_yaxis()
        ax.set_xlim(0, 108)
        ax.set_title(NAMES[treatment], loc='left', fontsize=13)
        for pos, row in enumerate(group.itertuples()):
            ax.text(101, pos, f'n={row.n_submuestras_completas}', va='center', fontsize=9)
        ax.spines[['top', 'right']].set_visible(False)
    axes[-1, 0].set_xticks([0, 20, 40, 60, 80, 100])
    axes[-1, 0].set_xlabel('Composición textural media de la parcela (%)')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.955), ncol=3, frameon=False)
    fig.suptitle('Caracterización textural por parcela', fontsize=16, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    save_figure(fig, out, 'composicion_textural_parcelas')


def plot_by_parcel(name: str, df: pd.DataFrame, summary: pd.DataFrame, out: Path) -> None:
    variables, parcels = VARIABLES[name], ordered_parcels(df)
    fig, axes = plt.subplots(len(variables), 1, figsize=(14, 3 * len(variables)), sharex=True)
    for ax, (variable, (label, unit)) in zip(np.atleast_1d(axes), variables.items()):
        for x, row in enumerate(parcels.itertuples()):
            group = df.loc[df['parcela'].eq(row.parcela)].sort_values('repeticion')
            values = group[variable]
            offsets = np.linspace(-0.19, 0.19, len(values)) if len(values) > 1 else [0]
            ax.scatter(x + np.asarray(offsets), values, s=28, color=COLORS[row.tratamiento], alpha=0.7, zorder=3)
            stat = summary.loc[summary['parcela'].eq(row.parcela) & summary['variable'].eq(variable)].iloc[0]
            if pd.notna(stat['media']):
                ax.plot(x, stat['media'], 'D', color='black', ms=5, zorder=5)
                if pd.notna(stat['de_submuestras']):
                    ax.errorbar(x, stat['media'], yerr=stat['de_submuestras'], fmt='none',
                                color='black', capsize=4, linewidth=1.2, zorder=4)
            ax.text(x, 0.98, f"n={stat['n_validos']}", transform=ax.get_xaxis_transform(),
                    ha='center', va='top', fontsize=8, color='#555555')
        ax.set_title(label, loc='left', fontsize=12)
        ax.set_ylabel(unit)
        ax.grid(axis='y', alpha=0.2)
        ax.margins(y=0.2)
        for boundary in range(1, len(parcels)):
            if parcels.iloc[boundary]['finca_id'] != parcels.iloc[boundary - 1]['finca_id']:
                ax.axvline(boundary - 0.5, color='#cccccc', lw=0.7)
    axes[-1].set_xticks(range(len(parcels)), [parcel_label(r, True) for r in parcels.itertuples()])
    axes[-1].set_xlabel('F = finca de la ficha de campo; cada parcela conserva su código original')
    handles = [Line2D([], [], color=c, marker='o', linestyle='', label=NAMES[t]) for t, c in COLORS.items()]
    handles.append(Line2D([], [], color='black', marker='D', linestyle='', label='Media de parcela ± DE de submuestras'))
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.962), ncol=3, frameon=False)
    fig.suptitle(f'{TITLES[name]} por finca y parcela', fontsize=16, y=0.997)
    fig.tight_layout(rect=(0, 0, 1, 0.935))
    save_figure(fig, out, f'{name}_por_lote')


def plot_subsamples(name: str, df: pd.DataFrame, out: Path) -> None:
    parcels, variables = ordered_parcels(df), VARIABLES[name]
    nrows = (len(variables) + 1) // 2
    fig, axes = plt.subplots(nrows, 2, figsize=(17, 6 * nrows), squeeze=False)
    repetitions = range(1, int(df['repeticion'].max()) + 1)
    for ax, (variable, (label, unit)) in zip(axes.flat, variables.items()):
        matrix = df.pivot(index='parcela', columns='repeticion', values=variable).reindex(
            index=parcels['parcela'], columns=repetitions)
        data = matrix.to_numpy(dtype=float)
        cmap = plt.get_cmap('YlGnBu').copy()
        cmap.set_bad('#ededed')
        im = ax.imshow(np.ma.masked_invalid(data), aspect='auto', cmap=cmap)
        finite = data[np.isfinite(data)]
        midpoint = (finite.min() + finite.max()) / 2 if finite.size else 0
        for (r, c), value in np.ndenumerate(data):
            ax.text(c, r, '—' if pd.isna(value) else f'{value:.2f}', ha='center', va='center', fontsize=8,
                    color='white' if pd.notna(value) and value > midpoint else '#222222')
        ax.set_xticks(range(len(repetitions)), [f'R{r}' for r in repetitions])
        ax.set_yticks(range(len(parcels)), [parcel_label(r) for r in parcels.itertuples()], fontsize=9)
        ax.set_xlabel('Submuestra dentro de cada parcela')
        ax.set_title(f'{label} ({unit})', loc='left')
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    for ax in list(axes.flat)[len(variables):]:
        ax.set_visible(False)
    fig.suptitle(f'{TITLES[name]}: valores por submuestra\nR no indica emparejamiento entre parcelas o análisis', fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure(fig, out, f'{name}_submuestras')


def plot_paired_differences(name: str, pairs: pd.DataFrame, out: Path) -> None:
    variables = VARIABLES[name]
    fig, axes = plt.subplots(1, len(variables), figsize=(5 * len(variables), 4.3), squeeze=False)
    for ax, (variable, (label, unit)) in zip(axes.flat, variables.items()):
        values = pairs.loc[pairs['variable'].eq(variable)].sort_values('finca_id')
        diff, y = values['diferencia_pina_menos_bosque'], np.arange(len(values))
        ax.axvline(0, color='#666666', lw=1)
        ax.hlines(y, 0, diff, color='#737373', lw=2)
        ax.scatter(diff, y, c=np.where(diff >= 0, COLORS['Pina'], COLORS['Bosque']), s=60, zorder=3)
        for pos, (_, row) in enumerate(values.iterrows()):
            delta = row['diferencia_pina_menos_bosque']
            if pd.notna(delta):
                ax.annotate(f'{delta:+.2f}', (delta, pos), xytext=(0, 9), textcoords='offset points', ha='center', fontsize=9)
        ax.set_yticks(y, [f'F{r.finca_id}: P{r.lote_pina}/B{r.lote_bosque}' for r in values.itertuples()])
        ax.set_ylim(len(values) - 0.5, -0.65)
        ax.margins(x=0.2)
        ax.set_title(label, fontsize=11, wrap=True)
        ax.set_xlabel('Piña − Bosque (' + ('puntos porcentuales' if unit == '%' else unit) + ')')
        ax.grid(axis='x', alpha=0.2)
    fig.suptitle(f'{TITLES[name]}: diferencia de medias dentro de finca\nCada punto compara dos parcelas; sin prueba de significancia', fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    save_figure(fig, out, f'{name}_comparacion_fincas')


def quality_checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    records = []

    def add(name, df, mask, variable, detail):
        for row in df.loc[mask.fillna(False)].itertuples():
            records.append({'tabla': name, 'id_lab': row.id_lab, 'parcela': row.parcela,
                            'repeticion': row.repeticion, 'variable': variable, 'observacion': detail})

    for name, df in tables.items():
        for variable, (_, unit) in VARIABLES[name].items():
            add(name, df, df[variable].isna(), variable, 'Valor faltante; excluido solo de este indicador.')
            # Un porcentaje gravimétrico usa masa seca como denominador y puede superar 100.
            if unit != '%':
                bad = df[variable] <= 0
            elif name == 'retencion_humedad':
                bad = df[variable] < 0
            else:
                bad = (df[variable] < 0) | (df[variable] > 100)
            add(name, df, bad, variable, 'Valor fuera del dominio físico esperado; se conserva para revisión.')
    df = tables['densidad_porosidad']
    expected = (1 - df['densidad_aparente_g_cm_3'] / df['densidad_particulas_g_cm_3']) * 100
    add('densidad_porosidad', df, (df['porosidad'] - expected).abs() > 0.1,
        'porosidad', 'No coincide con 100 × (1 − densidad aparente / densidad de partículas), tolerancia 0,1 pp.')
    df = tables['retencion_humedad']
    difference = df['humedad_gravimetrica_0_33_bar'] - df['humedad_gravimetrica_15_bar']
    add('retencion_humedad', df, (df['agua_util'] - difference).abs() > 0.05,
        'agua_util', 'No coincide con humedad a 0,33 bar − humedad a 15 bar, tolerancia 0,05 pp.')
    df = tables['textural']
    add('textural', df, (df[['arena', 'limo', 'arcilla']].sum(axis=1, min_count=3) - 100).abs() > 1,
        'textura', 'Arena + limo + arcilla difiere de 100 en más de 1 punto porcentual.')
    return pd.DataFrame(records, columns=['tabla', 'id_lab', 'parcela', 'repeticion', 'variable', 'observacion'])


def markdown_table(df: pd.DataFrame) -> str:
    def fmt(value):
        if pd.isna(value):
            return '—'
        if isinstance(value, (float, np.floating)):
            return f'{value:.2f}'
        return str(value).replace('|', '\\|').replace('\n', ' ')
    lines = ['| ' + ' | '.join(map(str, df.columns)) + ' |', '| ' + ' | '.join(['---'] * len(df.columns)) + ' |']
    lines += ['| ' + ' | '.join(fmt(v) for v in row) + ' |' for row in df.itertuples(index=False, name=None)]
    return '\n'.join(lines)


def characterization_sections(tables: dict[str, pd.DataFrame]) -> list[str]:
    sections = ['## Caracterización por parcela',
        'Cada caja corresponde a una parcela y cada punto a una de sus submuestras R. '
        'La caja abarca Q1–Q3, la línea interior es la mediana y el rombo negro es la media. '
        'Los bigotes llegan a las observaciones dentro de 1,5 veces el rango intercuartil desde la caja. '
        'Se dibujan **todos los puntos**, incluidos los que quedan más allá de los bigotes. '
        'Con tres submuestras, los puntos permiten leer los valores que forman los cuartiles.',
        'Las repeticiones mantienen su color y etiqueta dentro de cada figura. '
        'La escala vertical se ajusta a cada indicador y uso del suelo para mostrar su variación interna.',
        'Consulta también las [fichas individuales de las 12 parcelas](caracterizacion_parcelas.md), '
        'con media, DE, mediana, cuartiles, rango, CV y valores de cada repetición.']
    for treatment in CHARACTERIZATION_ORDER:
        sections.append(f'### {NAMES[treatment]}: distribución por parcela y repetición')
        for name in VARIABLES:
            if tables[name]['tratamiento'].eq(treatment).any():
                sections += [f'**{TITLES[name]}**',
                    f'![Boxplots de {NAMES[treatment]}: {TITLES[name]}]'
                    f'(figuras/agronomico/{name}_boxplot_{treatment.lower()}.png)']
    sections += ['### Variabilidad interna de las parcelas',
        'El coeficiente de variación (CV) expresa la DE como porcentaje de la media de cada parcela. '
        'Permite localizar qué parcelas presentan mayor dispersión relativa **para cada indicador**. '
        'Un CV alto no clasifica por sí solo la calidad del suelo. Un guion significa que el CV no es estimable.',
        '![CV por parcela e indicador](figuras/agronomico/variabilidad_interna_parcelas.png)',
        '### Composición textural de cada parcela',
        'Cada barra contiene los porcentajes medios de arena, limo y arcilla de una parcela. '
        'Se utilizan submuestras con las tres fracciones disponibles; `n` indica cuántas contribuyen a la barra. '
        'La dispersión de cada fracción se observa en los boxplots anteriores.',
        '![Composición textural por parcela](figuras/agronomico/composicion_textural_parcelas.png)']
    return sections


def write_parcel_profiles(tables, summary, docs_dir: Path = DOCS_DIR) -> None:
    sections = ['# Fichas de caracterización por parcela',
        '[Volver al análisis exploratorio y sus gráficos](analisis_exploratorio.md#caracterización-por-parcela).',
        '[Leer la interpretación agronómica de los resultados](interpretacion_agronomica.md).',
        'Cada ficha reúne los indicadores de una sola parcela. R identifica las submuestras dentro '
        'de cada análisis. El rango es mínimo–máximo, RIC = Q3 − Q1 y CV = 100 × DE / |media|. '
        'Los valores se presentan en la unidad de cada indicador; el CV está en %.']
    parcels = pd.concat([df[KEYS] for df in tables.values()]).drop_duplicates()
    ordered = pd.concat([ordered_parcels(parcels.loc[parcels['tratamiento'].eq(t)])
                         for t in CHARACTERIZATION_ORDER])
    sections.append('\n'.join(f'- [{parcel_label(r)}](#{r.parcela.lower()})' for r in ordered.itertuples()))
    for parcel in ordered.itertuples():
        stats = summary.loc[summary['parcela'].eq(parcel.parcela)]
        source = next(df.loc[df['parcela'].eq(parcel.parcela)].iloc[0]
                      for df in tables.values() if df['parcela'].eq(parcel.parcela).any())
        sections += [f'<a id="{parcel.parcela.lower()}"></a>', f'## {parcel_label(parcel)}',
                     f'Productor: {source["productor_ficha"]}. Código de parcela: `{parcel.parcela}`.']
        for name, variables in VARIABLES.items():
            group = tables[name].loc[tables[name]['parcela'].eq(parcel.parcela)].sort_values('repeticion')
            sections.append(f'### {TITLES[name]}')
            view = stats.loc[stats['tabla'].eq(name), ['indicador', 'unidad', 'n_validos',
                         'media', 'de_submuestras', 'mediana', 'q1', 'q3', 'rango_intercuartil',
                         'minimo', 'maximo', 'cv_submuestras_pct']]
            sections.append(markdown_table(view.rename(columns={
                'indicador': 'Indicador', 'unidad': 'Unidad', 'n_validos': 'n', 'media': 'Media',
                'de_submuestras': 'DE', 'mediana': 'Mediana', 'q1': 'Q1', 'q3': 'Q3',
                'rango_intercuartil': 'RIC', 'minimo': 'Mín.', 'maximo': 'Máx.', 'cv_submuestras_pct': 'CV (%)'})))
            individual = group[['repeticion', 'id_lab'] + list(variables)].copy()
            individual['repeticion'] = individual['repeticion'].map(lambda r: f'R{r}')
            sections += ['**Valores de las submuestras**', markdown_table(individual.rename(columns={
                'repeticion': 'Submuestra', 'id_lab': 'ID LAB',
                **{v: f'{label} ({unit})' for v, (label, unit) in variables.items()}}))]
    (docs_dir / 'caracterizacion_parcelas.md').write_text('\n\n'.join(sections) + '\n', encoding='utf-8')


def observed_patterns(tables: dict[str, pd.DataFrame], summary: pd.DataFrame, pairs: pd.DataFrame) -> str:
    lines = []
    for variable in ['densidad_aparente_g_cm_3', 'porosidad', 'agua_util']:
        values = pairs.loc[pairs['variable'].eq(variable)].dropna(subset=['diferencia_pina_menos_bosque'])
        if values.empty:
            continue
        delta = values['diferencia_pina_menos_bosque']
        lines.append(f'- **{values.iloc[0]["indicador"]}:** la media de Piña es mayor que la de Bosque '
                     f'en {int((delta > 0).sum())} y menor en {int((delta < 0).sum())} de las '
                     f'{len(values)} fincas comparables; Δ varía de {delta.min():+.2f} a '
                     f'{delta.max():+.2f} {values.iloc[0]["unidad_diferencia"]}.')
    stability = summary.loc[summary['variable'].eq('estabilidad_de_agregados')].dropna(subset=['cv_submuestras_pct'])
    if not stability.empty:
        extreme = stability.loc[stability['cv_submuestras_pct'].idxmax()]
        individual = tables['textural'].loc[tables['textural']['parcela'].eq(extreme['parcela'])].sort_values('repeticion')
        values_text = '; '.join(f'R{r.repeticion} = {r.estabilidad_de_agregados:.2f} %' for r in individual.itertuples())
        lines.append(f'- **Variación entre submuestras:** {NAMES[extreme["tratamiento"]]} {extreme["lote"]} '
                     f'(F{extreme["finca_id"]}) presenta el mayor CV de estabilidad de agregados '
                     f'({extreme["cv_submuestras_pct"]:.2f} %): {values_text}. '
                     'El boxplot y la ficha individual permiten observar esta dispersión.')
    lines.append('- Estos patrones describen las parcelas observadas; no constituyen pruebas de significancia ni de causalidad.')
    return '\n'.join(lines)


def write_report(tables, summary, pairs, checks, docs_dir: Path = DOCS_DIR) -> None:
    design = pd.read_csv(ROOT / 'processed' / 'diseno_muestreo.csv')
    audit = pd.read_csv(ROOT / 'processed' / 'auditoria_preparacion.csv')
    sections = [
        '# Exploración agronómica y caracterización por parcela',
        'El análisis comienza con la **caracterización individual de las parcelas de Bosque y Piña**: '
        'distribución de los valores, variación entre repeticiones y composición textural. '
        'Después presenta las comparaciones entre parcelas y usos del suelo dentro de finca. '
        '**Se asume la coherencia metodológica del muestreo**, según la indicación del responsable del estudio. '
        'R1, R2, etc. identifican submuestras de una misma parcela.',
        '[Leer la interpretación agronómica de los resultados](interpretacion_agronomica.md).',
        '## Cómo leer los resultados',
        '- **Entre lotes:** cada parcela conserva su identidad; no se promedian todas las fincas por zona.\n'
        '- **Entre tratamientos/usos:** se comparan las medias de Piña y Bosque dentro de la finca '
        'que corresponde en la ficha de campo.\n'
        '- **Entre repeticiones:** los puntos y los mapas de valores muestran las submuestras R de cada parcela.\n'
        '- **Dispersión:** las barras son media ± desviación estándar (DE) de submuestras, '
        'no intervalos de confianza ni error experimental entre parcelas. `n` cuenta submuestras con dato.\n'
        '- **Diferencia:** Δ = media de Piña − media de Bosque; para variables en %, Δ se expresa '
        'en puntos porcentuales. El cambio relativo (%) es 100 × Δ / media de Bosque.',
        *characterization_sections(tables),
        '## Diseño de muestreo recuperado',
        'La correspondencia procede de [PIÑA FINCAS PRODUCTORAS .xlsx](../raw/pina/PIÑA%20FINCAS%20PRODUCTORAS%20.xlsx). '
        'Los números de Bosque y Piña pertenecen a series distintas. Por ejemplo, **Bosque 2 corresponde '
        'a la finca 3, con Piña 3**, y no a Piña 2. `lote` conserva el número original; `finca_id` '
        'identifica la correspondencia de campo; `parcela` combina uso y lote.',
    ]
    field_rows = []
    for finca, group in design.groupby('finca_id'):
        labels = {r.tratamiento: f'{NAMES[r.tratamiento]} {r.lote}' for r in group.itertuples()}
        field_rows.append({'Finca': finca, 'Piña': labels.get('Pina', 'Sin parcela'),
                           'Bosque': labels.get('Bosque', 'Sin parcela'),
                           'Productor (ficha)': group.iloc[0]['productor_ficha']})
    sections += [markdown_table(pd.DataFrame(field_rows)),
        'Hay **8 parcelas de Piña y 4 de Bosque**, distribuidas en 8 códigos de finca. Solo las fincas '
        '**1, 3, 4 y 5** tienen ambos usos. Las fincas **4 y 5 pertenecen al mismo productor (Sergio Rojas)**: '
        'las cuatro comparaciones corresponden a tres productores. '
        'Las fincas 2, 6, 7 y 8 se describen sin asignarles un bosque de otra finca.',
        'La base contiene 8 submuestras por parcela para densidad/porosidad y 3 para textura/estabilidad '
        'y retención de humedad. Las relaciones entre mediciones individuales se establecen por ID LAB, '
        'no solo por el número R. Textura y retención comparten '
        f'{len(set(tables["textural"]["id_lab"]) & set(tables["retencion_humedad"]["id_lab"]))} ID LAB. '
        'Las comparaciones Piña–Bosque utilizan las medias de las parcelas correspondientes.',
        '## Auditoría de preparación', markdown_table(audit.rename(columns={
            'tabla': 'Tabla', 'filas_entrada': 'Filas de origen', 'muestras_unicas': 'Muestras únicas',
            'copias_consolidadas': 'Copias consolidadas', 'submuestras_formato_guion': 'IDs con formato lote-submuestra'})),
        'Se recuperó el número de submuestra en los identificadores `Piña 1-1` y `Bosque 1-1` '
        '(y sus secuencias), antes guardado como productor. Las copias de Piña 8 en textura y '
        'retención tenían el mismo ID LAB y los mismos resultados: se cuenta una sola muestra '
        'y se conservan ambas procedencias. Resultados discordantes para un mismo ID LAB detienen '
        'la preparación. Los archivos de origen permanecen intactos.',
        f'Controles de faltantes, dominios físicos y consistencia de variables calculadas: '
        f'**{len(checks)} observaciones para revisar**. '
        'Estos controles no sustituyen la revisión de laboratorio ni eliminan valores extremos.',
    ]
    if not checks.empty:
        sections.append(markdown_table(checks))
    coverage = [df.groupby(KEYS).size().rename(name) for name, df in tables.items()]
    coverage_frame = pd.concat(coverage, axis=1).reset_index().sort_values(['finca_id', 'tratamiento'])
    coverage_frame['tratamiento'] = coverage_frame['tratamiento'].map(NAMES)
    sections += ['## Cobertura de submuestras por parcela', markdown_table(coverage_frame),
                 '## Comparaciones complementarias entre parcelas',
                 observed_patterns(tables, summary, pairs)]
    for name, variables in VARIABLES.items():
        stats = summary.loc[summary['tabla'].eq(name)]
        contrasts = pairs.loc[pairs['tabla'].eq(name)]
        sections += [f'### {TITLES[name]}',
            f'![{TITLES[name]} por parcela](figuras/agronomico/{name}_por_lote.png)',
            'Diamantes negros: medias de parcela. Barras: ± DE entre submuestras. '
            'Puntos de color: observaciones individuales; su desplazamiento horizontal solo evita superposición.',
            f'![Valores por submuestra](figuras/agronomico/{name}_submuestras.png)',
            'Cada fila es una parcela y cada columna una submuestra. La escala de color es propia de cada '
            'indicador. Un guion representa una combinación sin dato; no equivale a cero.',
            f'![Diferencias dentro de finca](figuras/agronomico/{name}_comparacion_fincas.png)',
        ]
        readings = []
        for variable, (label, unit) in variables.items():
            valid = stats.loc[stats['variable'].eq(variable)].dropna(subset=['media'])
            if valid.empty:
                continue
            low, high = valid.loc[valid['media'].idxmin()], valid.loc[valid['media'].idxmax()]
            readings.append(f'- **{label}:** las medias de parcela van de {low["media"]:.2f} {unit} '
                f'({NAMES[low["tratamiento"]]} {low["lote"]}, F{low["finca_id"]}) a '
                f'{high["media"]:.2f} {unit} ({NAMES[high["tratamiento"]]} {high["lote"]}, F{high["finca_id"]}).')
        sections.append('\n'.join(readings))
        sections.append('#### Medias y variación dentro de cada parcela')
        compact = []
        for row in ordered_parcels(tables[name]).itertuples():
            result = {'Finca / parcela': parcel_label(row)}
            for variable, (label, unit) in variables.items():
                stat = stats.loc[stats['parcela'].eq(row.parcela) & stats['variable'].eq(variable)].iloc[0]
                if stat['n_validos'] == 0:
                    value = 'Sin dato (n=0)'
                elif stat['n_validos'] == 1:
                    value = f'{stat["media"]:.2f}; DE no estimable (n=1)'
                else:
                    value = f'{stat["media"]:.2f} ± {stat["de_submuestras"]:.2f} (n={stat["n_validos"]})'
                result[f'{label} ({unit})'] = value
            compact.append(result)
        sections.append(markdown_table(pd.DataFrame(compact)))
        sections.append('#### Diferencias Piña − Bosque dentro de finca')
        view = contrasts[['finca_id', 'indicador', 'media_pina', 'media_bosque',
                          'diferencia_pina_menos_bosque', 'unidad_diferencia', 'cambio_relativo_pct']]
        sections.append(markdown_table(view.rename(columns={'finca_id': 'Finca', 'indicador': 'Indicador',
            'media_pina': 'Media Piña', 'media_bosque': 'Media Bosque',
            'diferencia_pina_menos_bosque': 'Δ Piña − Bosque', 'unidad_diferencia': 'Unidad de Δ',
            'cambio_relativo_pct': 'Cambio relativo (%)'})))
    sections += ['## Lectura agronómica y alcance',
        'La exploración permite localizar parcelas con valores distintos y verificar si la dirección '
        'de la diferencia Piña–Bosque se repite entre fincas. La textura describe el contexto de cada '
        'parcela; no se interpreta toda diferencia como un efecto del manejo. La porosidad se calcula '
        'a partir de las densidades y el agua útil como diferencia de las dos humedades: no son '
        'mediciones independientes de sus componentes.',
        'La humedad y el agua útil permanecen en base **gravimétrica**. La conversión a humedad '
        'volumétrica requiere una densidad aparente compatible con el muestreo; para expresar una '
        'lámina de agua se necesita además la profundidad de suelo representada.',
        'Esta etapa es **descriptiva**: caracteriza las parcelas y sus submuestras. '
        'La media y la mediana describen el nivel de cada indicador; la DE, los cuartiles, el rango '
        'y el CV describen su dispersión dentro de parcela. Las comparaciones entre usos complementan '
        'esta caracterización. La inferencia estadística corresponde a una etapa posterior que '
        'represente la estructura de fincas, parcelas y submuestras.',
        '## Archivos y reproducción',
        '- [Diseño de muestreo](../processed/diseno_muestreo.csv).\n'
        '- [Resumen por parcela e indicador](../processed/analisis_listo/resumenes/resumen_por_parcela.csv): n válido, faltantes, media, '
        'DE, mediana, Q1, Q3, rango intercuartil, mínimo, máximo, amplitud y CV de submuestras; '
        'el CV no es el CV residual de un ANOVA.\n'
        '- [Fichas individuales por parcela](caracterizacion_parcelas.md), con resúmenes y repeticiones.\n'
        '- [Composición textural por parcela](../processed/analisis_listo/resumenes/composicion_textural_por_parcela.csv).\n'
        '- [Comparaciones dentro de finca](../processed/analisis_listo/resumenes/comparaciones_pina_bosque.csv).\n'
        '- [Valores individuales](../processed/analisis_listo/resumenes/valores_por_submuestra.csv), con ID LAB y procedencia.\n'
        '- [Clases texturales por parcela](../processed/analisis_listo/resumenes/clases_texturales.csv).\n'
        '- [Controles de calidad](../processed/analisis_listo/resumenes/controles_calidad.csv).\n'
        '- [Auditoría de preparación](../processed/auditoria_preparacion.csv) y '
        '[registros de duplicados](../processed/duplicados_consolidados.csv).\n'
        '- Figuras en `docs/figuras/agronomico/`, en PNG y SVG para exportación. '
        'Las figuras antiguas de `docs/figuras/historico/` no forman parte de este informe.',
        'Desde la raíz del proyecto, con el entorno de Python activado:',
        '```powershell\npython src/01_soil_data_pipeline.py\n'
        'python src/03_exploratory_analysis.py\n```',
    ]
    (docs_dir / 'analisis_exploratorio.md').write_text('\n\n'.join(sections) + '\n', encoding='utf-8')


def main() -> None:
    tables = load_tables()
    figures, outputs = DOCS_DIR / 'figuras' / 'agronomico', SUMMARY_DIR
    figures.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    summary, pairs = build_summaries(tables)
    checks = quality_checks(tables)
    summary.to_csv(outputs / 'resumen_por_parcela.csv', index=False)
    pairs.to_csv(outputs / 'comparaciones_pina_bosque.csv', index=False)
    checks.to_csv(outputs / 'controles_calidad.csv', index=False)
    long_tables = []
    for name, df in tables.items():
        long = df.melt(id_vars=KEYS + ['repeticion', 'id_lab', 'id_usuario', 'xls_origen'],
                       value_vars=list(VARIABLES[name]), var_name='variable', value_name='valor')
        long.insert(0, 'tabla', name)
        long['unidad'] = long['variable'].map({v: info[1] for v, info in VARIABLES[name].items()})
        long_tables.append(long)
        for treatment in CHARACTERIZATION_ORDER:
            plot_parcel_boxplots(name, df, treatment, figures)
        plot_by_parcel(name, df, summary.loc[summary['tabla'].eq(name)], figures)
        plot_subsamples(name, df, figures)
        plot_paired_differences(name, pairs.loc[pairs['tabla'].eq(name)], figures)
    pd.concat(long_tables, ignore_index=True).to_csv(outputs / 'valores_por_submuestra.csv', index=False)
    classes = tables['textural'].groupby(KEYS + ['clase_textural'], dropna=False).size().rename('n_submuestras').reset_index()
    classes.to_csv(outputs / 'clases_texturales.csv', index=False)
    composition = textural_composition(tables['textural'])
    composition.to_csv(outputs / 'composicion_textural_por_parcela.csv', index=False)
    plot_textural_composition(composition, figures)
    plot_internal_variability(summary, figures)
    write_parcel_profiles(tables, summary)
    write_report(tables, summary, pairs, checks)
    print(f'Informe: {DOCS_DIR / "analisis_exploratorio.md"}')
    print(f'Tablas CSV: {outputs}')
    print(f'{len(summary)} resúmenes de parcela, {len(pairs)} comparaciones y {len(checks)} observaciones de calidad.')
    print(f'Figuras PNG/SVG: {figures}')


if __name__ == '__main__':
    main()
