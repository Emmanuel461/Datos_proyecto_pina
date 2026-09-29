const configs = {
  densidad_porosidad: {
    file: '../processed/analisis_listo/web/densidad_porosidad.csv',
    title: 'Densidad y porosidad',
    vars: {
      densidad_aparente_g_cm_3: ['Densidad aparente', 'g/cm³'],
      densidad_particulas_g_cm_3: ['Densidad de partículas', 'g/cm³'],
      porosidad: ['Porosidad', '%']
    }
  },
  retencion_humedad: {
    file: '../processed/analisis_listo/web/retencion_humedad.csv',
    title: 'Retención de humedad',
    vars: {
      humedad_gravimetrica_0_33_bar: ['Humedad gravimétrica · 0,33 bar', '%'],
      humedad_gravimetrica_15_bar: ['Humedad gravimétrica · 15 bar', '%'],
      agua_util: ['Agua útil gravimétrica', '%']
    }
  },
  textural: {
    file: '../processed/analisis_listo/web/textural.csv',
    title: 'Textura y estabilidad',
    vars: {
      arena: ['Arena', '%'],
      limo: ['Limo', '%'],
      arcilla: ['Arcilla', '%'],
      estabilidad_de_agregados: ['Estabilidad de agregados', '%']
    }
  }
};
const chemicalVariables = {
  ph: ['pH (H₂O)', 'adimensional'],
  acidez: ['Acidez', 'cmol(+)/L'],
  ca: ['Calcio (Ca)', 'cmol(+)/L'],
  mg: ['Magnesio (Mg)', 'cmol(+)/L'],
  k: ['Potasio (K)', 'cmol(+)/L'],
  cice: ['CICE', 'cmol(+)/L'],
  sa: ['Saturación de acidez (SA)', '%'],
  p: ['Fósforo (P)', 'mg/L'],
  zn: ['Zinc (Zn)', 'mg/L'],
  cu: ['Cobre (Cu)', 'mg/L'],
  fe: ['Hierro (Fe)', 'mg/L'],
  mn: ['Manganeso (Mn)', 'mg/L'],
  ce: ['Conductividad eléctrica (CE)', 'mS/cm'],
  c: ['Carbono (C)', '%'],
  n: ['Nitrógeno (N)', '%'],
  c_n: ['Relación C/N', 'adimensional']
};
const chemicalConfig = {
  file: '../processed/quimico_analisis_listo/web/resultados_quimicos.csv',
  title: 'Análisis químico', vars: chemicalVariables
};

const COLORS = { Pina: '#bf801a', Bosque: '#24745b' };
let data = [];
let cfg;
let field;
let currentModule = 'physical';
let loadVersion = 0;
let ready = false;
const $ = id => document.getElementById(id);
const treatmentName = value => value === 'Pina' ? 'Pi\u00f1a' : value;
const parcelName = record => `${treatmentName(record.tratamiento)} ${record.lote}`;
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
const isNumber = value => String(value).trim() !== '' && Number.isFinite(Number(value));

async function readRecords(file) {
  if (location.protocol === 'file:') {
    throw new Error('La página se abrió como archivo local (file://). El navegador bloquea la lectura de los CSV en este modo. ' +
      'Desde la carpeta Datos ejecuta: python -m http.server 8000. Después abre http://localhost:8000/ en el navegador.');
  }
  const url = new URL(file, document.baseURI);
  let response;
  let text;
  try {
    response = await fetch(url, { cache: 'no-cache' });
    if (response.ok) text = await response.text();
  } catch (error) {
    throw new Error(`No se pudo acceder a ${url.href}. Comprueba que el servidor siga activo y que haya conexión.`, { cause: error });
  }
  const publicationHint = location.hostname.endsWith('.github.io')
    ? 'En GitHub Pages selecciona / (root) y sube también los CSV de las subcarpetas processed/.../web/.'
    : 'Sirve la raíz de Datos, que contiene tanto docs/ como processed/.';
  if (!response.ok) {
    const script = file.includes('quimico_analisis_listo') ? '04_prepare_chemical_data.py' : '01_soil_data_pipeline.py';
    const missingHint = response.status === 404
      ? `Genera el CSV con python src/${script}. ${publicationHint}`
      : 'Comprueba los permisos y la disponibilidad del servidor.';
    throw new Error(`No se pudo cargar ${url.href} (HTTP ${response.status}). ${missingHint}`);
  }
  if (/^\s*(?:<!doctype\s+html|<html[\s>])/i.test(text)) {
    throw new Error(`El servidor devolvió una página HTML en lugar del CSV ${file}. ${publicationHint}`);
  }
  return parseCsv(text);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"' && quoted && text[i + 1] === '"') {
      cell += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === ',' && !quoted) {
      row.push(cell);
      cell = '';
    } else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[i + 1] === '\n') i += 1;
      row.push(cell);
      if (row.some(value => value !== '')) rows.push(row);
      row = [];
      cell = '';
    } else {
      cell += char;
    }
  }
  if (quoted) throw new Error('El CSV contiene comillas sin cerrar.');
  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }
  const headers = (rows.shift() || []).map(value => value.replace(/^\uFEFF/, ''));
  if (!headers.length || headers.some(header => !header) || new Set(headers).size !== headers.length) {
    throw new Error('El CSV no contiene encabezados válidos y únicos.');
  }
  if (!rows.length) throw new Error('El CSV no contiene resultados.');
  return rows.map((values, index) => {
    if (values.length !== headers.length) throw new Error(`Número de columnas incorrecto en la fila ${index + 2}.`);
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
  });
}

function validateData(records, config, physical) {
  const required = physical
    ? ['tratamiento', 'finca_id', 'lote', 'repeticion', 'parcela', ...Object.keys(config.vars)]
    : ['tratamiento', 'finca_id', 'lote', 'parcela', 'variable', 'unidad', 'resultado_original', 'valor', 'operador', 'limite_reportado', 'estado'];
  const seen = new Set();
  const assignments = new Map();
  for (const record of records) {
    if (required.some(column => !(column in record))) throw new Error(`${config.file}: faltan columnas requeridas.`);
    const identifiers = physical ? ['finca_id', 'lote', 'repeticion'] : ['finca_id', 'lote'];
    if (!Object.hasOwn(COLORS, record.tratamiento) || identifiers.some(key => !/^[1-9]\d*$/.test(record[key])) ||
        record.parcela !== `${record.tratamiento}_${record.lote}`) {
      throw new Error(`${config.file}: identificación de parcela inválida.`);
    }
    if (assignments.has(record.parcela) && assignments.get(record.parcela) !== record.finca_id) {
      throw new Error(`${config.file}: una parcela tiene varias fincas asignadas.`);
    }
    assignments.set(record.parcela, record.finca_id);
    const key = `${record.parcela}|${physical ? record.repeticion : record.variable}`;
    if (seen.has(key)) throw new Error(`${config.file}: resultado duplicado para ${key}.`);
    seen.add(key);
    if (physical) {
      if (Object.keys(config.vars).some(variable => record[variable] !== '' && !isNumber(record[variable]))) {
        throw new Error(`${config.file}: resultado físico no numérico.`);
      }
    } else {
      if (!Object.hasOwn(chemicalVariables, record.variable) || record.unidad !== chemicalVariables[record.variable][1]) {
        throw new Error(`${config.file}: variable o unidad química no reconocida.`);
      }
      const valid = record.estado === 'cuantificado'
        ? isNumber(record.valor) && Number(record.valor) >= 0 && record.operador === '=' && record.limite_reportado === ''
        : record.estado === 'censurado'
          ? record.valor === '' && isNumber(record.limite_reportado) && Number(record.limite_reportado) >= 0 && ['<', '<=', '>', '>='].includes(record.operador)
          : record.estado === 'faltante' && record.valor === '' && record.limite_reportado === '' && record.operador === '';
      if (!valid) throw new Error(`${config.file}: estado y resultado incompatibles para ${key}.`);
    }
  }
  if (!physical) {
    const variables = Object.keys(chemicalVariables);
    for (const parcel of assignments.keys()) {
      if (variables.some(variable => !seen.has(`${parcel}|${variable}`))) {
        throw new Error(`${config.file}: faltan registros de variables para ${parcel}.`);
      }
    }
  }
}

async function load(version) {
  const physical = currentModule === 'physical';
  const key = $('dataset').value;
  const nextConfig = physical ? configs[key] : chemicalConfig;
  const records = await readRecords(nextConfig.file);
  if (version !== loadVersion) return;
  validateData(records, nextConfig, physical);
  cfg = { ...nextConfig };
  data = records;
  if (!physical) {
    const available = new Set(data.map(record => record.variable));
    cfg.vars = Object.fromEntries(Object.entries(chemicalVariables).filter(([variable]) => available.has(variable)));
  }
  field = Object.keys(cfg.vars)[0];
  fillVars();
  fillFilters();
  $('dataset-label').hidden = !physical;
  $('sample-heading').textContent = 'Repetición (R)';
  $('sample-heading').hidden = !physical;
  $('result-heading').textContent = 'Valor';
  $('n-label').textContent = physical ? 'Repeticiones con valor' : 'Parcelas visibles';
  $('mean-label').textContent = 'Media (promedio)';
  $('median-label').textContent = 'Mediana';
  $('range-label').textContent = 'Rango (mínimo–máximo)';
  $('chemical-note').hidden = physical;
  $('chart-subtitle').textContent = physical
    ? 'Cada punto representa una repetición (R) de una parcela en este análisis. Los resúmenes describen los datos filtrados.'
    : 'Distribución de valores entre parcelas; cada punto corresponde a una muestra de laboratorio.';
  document.querySelector('footer').textContent = physical
    ? 'Fuente: tablas de processed/analisis_listo/; lectura de las columnas públicas en processed/analisis_listo/web/.'
    : 'Fuente: processed/quimico_analisis_listo/resultados_quimicos.csv; lectura de las columnas públicas en processed/quimico_analisis_listo/web/. Fincas vinculadas mediante el diseño de muestreo.';
}

function fillVars() {
  $('variable').innerHTML = Object.entries(cfg.vars)
    .map(([key, value]) => `<option value="${key}">${value[0]}</option>`).join('');
  $('chart-title').textContent = cfg.title;
}

function fillFilters() {
  const treatments = [...new Set(data.map(record => record.tratamiento))].filter(Boolean);
  const farms = [...new Set(data.map(record => record.finca_id))].filter(Boolean)
    .sort((a, b) => Number(a) - Number(b));
  const producers = new Map();
  for (const record of data) {
    const name = (record.productor_finca || '').trim();
    if (!name) continue;
    if (producers.has(record.finca_id) && producers.get(record.finca_id) !== name) {
      throw new Error(`Hay nombres de productor distintos para la finca ${record.finca_id}. Revisa la ficha de fincas.`);
    }
    producers.set(record.finca_id, name);
  }
  $('treatment').innerHTML = '<option value="all">Todos</option>' + treatments
    .map(value => `<option value="${value}">${treatmentName(value)}</option>`).join('');
  $('farm').innerHTML = '<option value="all">Todas</option>' + farms
    .map(value => `<option value="${value}">Finca ${value}${producers.has(value) ? ` — ${escapeHtml(producers.get(value))}` : ''}</option>`).join('');
  $('farm-reference-rows').innerHTML = farms.map(value =>
    `<tr><td>Finca ${value}</td><td>${escapeHtml(producers.get(value) || 'Nombre no disponible en los datos cargados')}</td></tr>`
  ).join('');
}

async function loadAvailability(version) {
  const tables = [
    { ...configs.densidad_porosidad, physical: true },
    { ...configs.retencion_humedad, physical: true },
    { ...configs.textural, physical: true },
    { ...chemicalConfig, physical: false }
  ];
  // Cada tabla se lee por separado: no hay uniones ni comparaciones por R.
  const results = await Promise.allSettled(tables.map(async table => {
    const records = await readRecords(table.file);
    validateData(records, table, table.physical);
    return records;
  }));
  if (version !== loadVersion) return;
  const parcels = new Map();
  tables.forEach((table, index) => {
    const result = results[index];
    table.byParcel = new Map();
    if (result.status === 'rejected') {
      table.error = result.reason.message;
      return;
    }
    for (const record of result.value) {
      if (!parcels.has(record.parcela)) {
        parcels.set(record.parcela, { finca: record.finca_id, tratamiento: record.tratamiento, lote: record.lote });
      } else if (parcels.get(record.parcela).finca !== record.finca_id) {
        throw new Error(`La finca de ${parcelName(record)} difiere entre las tablas; revisa el diseño de muestreo.`);
      }
      if (!table.byParcel.has(record.parcela)) table.byParcel.set(record.parcela, []);
      table.byParcel.get(record.parcela).push(record);
    }
  });
  const unavailable = tables.filter(table => table.error);
  $('availability-warning').hidden = unavailable.length === 0;
  $('availability-warning').textContent = unavailable.map(table => `${table.title}: ${table.error}`).join(' ');
  const ordered = [...parcels.entries()].sort((a, b) =>
    Number(a[1].finca) - Number(b[1].finca) || a[1].tratamiento.localeCompare(b[1].tratamiento)
  );
  $('coverage-rows').innerHTML = ordered.map(([parcelId, parcel]) => {
    const notes = [];
    const counts = tables.map(table => {
      if (table.error) return 'Archivo no disponible';
      const subset = table.byParcel.get(parcelId) || [];
      if (!subset.length) {
        notes.push(`${table.title}: sin registros para esta parcela.`);
        return 'Sin registros';
      }
      Object.entries(table.vars).forEach(([variable, [label]]) => {
        const missing = table.physical
          ? subset.filter(record => record[variable] === '').length
          : subset.filter(record => record.variable === variable && record.estado === 'faltante').length;
        if (missing) notes.push(table.physical
          ? `${table.title} · ${label}: ${missing} de ${subset.length} repeticiones sin valor reportado.`
          : `${table.title} · ${label}: sin valor reportado.`);
      });
      if (table.physical) return `${subset.length} ${subset.length === 1 ? 'repetición' : 'repeticiones'}`;
      // El formato químico tiene una fila por indicador, no por muestra.
      const reported = subset.filter(record => record.estado !== 'faltante').length;
      return `1 muestra de laboratorio<br>${reported} de ${Object.keys(table.vars).length} indicadores con resultado`;
    });
    const detail = notes.length ? notes.map(escapeHtml).join('<br>')
      : 'Sin valores faltantes en los análisis disponibles.';
    return `<tr><td>Finca ${parcel.finca}</td><td>${treatmentName(parcel.tratamiento)} ${parcel.lote}</td>` +
      counts.map(count => `<td>${count}</td>`).join('') + `<td>${detail}</td></tr>`;
  }).join('') || '<tr><td colspan="7">No se pudo consultar la disponibilidad de los análisis.</td></tr>';
}

function categoryLabel(record, group) {
  if (group === 'tratamiento') return treatmentName(record.tratamiento);
  if (group === 'finca_id') return `Finca ${record.finca_id}`;
  return `Finca ${record.finca_id} · ${treatmentName(record.tratamiento)} ${record.lote}`;
}

function render() {
  if (!ready) return;
  field = $('variable').value;
  $('result-heading').textContent = `Valor — ${cfg.vars[field][0]}`;
  if (currentModule === 'chemical') return renderChemical();
  const rows = data.filter(record =>
    ($('treatment').value === 'all' || record.tratamiento === $('treatment').value) &&
    ($('farm').value === 'all' || record.finca_id === $('farm').value) &&
    record[field] !== '' && record[field] != null && Number.isFinite(Number(record[field]))
  );
  const numbers = rows.map(record => Number(record[field]));
  const unit = cfg.vars[field][1];
  const sorted = [...numbers].sort((a, b) => a - b);
  const median = sorted.length
    ? sorted.length % 2 ? sorted[(sorted.length - 1) / 2]
      : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
    : null;
  $('n').textContent = numbers.length;
  $('n-note').textContent = `${new Set(rows.map(record => record.parcela)).size} parcelas · R = repetición dentro de cada parcela y análisis`;
  $('chart-title').textContent = cfg.vars[field][0];
  $('mean').textContent = numbers.length
    ? `${(numbers.reduce((sum, value) => sum + value, 0) / numbers.length).toFixed(2)} ${unit}` : '—';
  $('median').textContent = median == null ? '—' : `${median.toFixed(2)} ${unit}`;
  $('range').textContent = sorted.length ? `${sorted[0].toFixed(2)} – ${sorted.at(-1).toFixed(2)} ${unit}` : '—';

  const group = $('group').value;
  const treatments = [...new Set(rows.map(record => record.tratamiento))];
  const traces = treatments.map(treatment => {
    const subset = rows.filter(record => record.tratamiento === treatment);
    return {
      type: 'box',
      name: treatmentName(treatment),
      x: subset.map(record => categoryLabel(record, group)),
      y: subset.map(record => Number(record[field])),
      boxpoints: 'all',
      quartilemethod: 'linear',
      customdata: subset.map(record => [parcelName(record), `Repetición ${record.repeticion} (R${record.repeticion})`, record.finca_id]),
      hovertemplate: '%{customdata[0]} · %{customdata[1]}<br>Finca %{customdata[2]}<br>%{y} ' + unit + '<extra>%{fullData.name}</extra>',
      jitter: 0.28,
      pointpos: 0,
      marker: { color: COLORS[treatment] },
      line: { color: COLORS[treatment] }
    };
  });
  Plotly.react('chart', traces, {
    autosize: true, boxmode: 'group',
    paper_bgcolor: 'white',
    plot_bgcolor: 'white',
    font: { color: '#17251f' },
    yaxis: { title: `${cfg.vars[field][0]} (${unit})`, gridcolor: '#e5ece7' },
    xaxis: { title: $('group').selectedOptions[0].text, tickangle: -30, automargin: true },
    margin: { t: 24, r: 24, b: 110, l: 75 },
    legend: { orientation: 'h', y: 1.12 },
    showlegend: treatments.length > 1,
    annotations: rows.length ? [] : [{ text: 'No hay datos para estos filtros.', x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', showarrow: false }]
  }, { responsive: true, displaylogo: false });

  $('rows').innerHTML = rows.map(record =>
    `<tr><td>${treatmentName(record.tratamiento)}</td><td>${record.finca_id}</td>` +
    `<td>${treatmentName(record.tratamiento)} ${record.lote}</td><td>R${record.repeticion}</td>` +
    `<td>${Number(record[field]).toFixed(2)} ${unit}</td></tr>`
  ).join('') || '<tr><td colspan="5">No hay datos para estos filtros.</td></tr>';
}

function renderChemical() {
  field = $('variable').value;
  const rows = data.filter(record =>
    record.variable === field &&
    ($('treatment').value === 'all' || record.tratamiento === $('treatment').value) &&
    ($('farm').value === 'all' || record.finca_id === $('farm').value)
  );
  const measured = rows.filter(record => record.estado === 'cuantificado' && record.valor !== '');
  const censored = rows.filter(record => record.estado === 'censurado' && record.limite_reportado !== '');
  const missing = rows.filter(record => record.estado === 'faltante');
  const values = measured.map(record => Number(record.valor)).filter(Number.isFinite);
  const sorted = [...values].sort((a, b) => a - b);
  const median = sorted.length
    ? sorted.length % 2 ? sorted[(sorted.length - 1) / 2]
      : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
    : null;
  const unit = cfg.vars[field][1];
  $('chart-title').textContent = cfg.vars[field][0];
  $('n').textContent = rows.length;
  $('n-note').textContent = `${measured.length} valores numéricos · ${censored.length} reportados como límite · ${missing.length} sin resultado`;
  $('mean').textContent = values.length
    ? `${(values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2)} ${unit}` : '—';
  $('median').textContent = median == null ? '—' : `${median.toFixed(2)} ${unit}`;
  $('range').textContent = sorted.length ? `${sorted[0].toFixed(2)} – ${sorted.at(-1).toFixed(2)} ${unit}` : '—';
  $('chemical-note').textContent = 'El reporte químico actual tiene una muestra de laboratorio por parcela y no incluye repeticiones R. ' +
    'Los indicadores (pH, calcio, etc.) son distintas variables medidas en esa muestra. ' +
    'Los resultados como «<1» se muestran con un símbolo distinto en el límite indicado ' +
    'y quedan fuera de las cajas y del cálculo de la media, la mediana y el rango.';

  const group = $('group').value;
  const treatments = [...new Set(rows.map(record => record.tratamiento))];
  const categories = [...new Set([...rows].sort((a, b) => Number(a.finca_id) - Number(b.finca_id) ||
    a.tratamiento.localeCompare(b.tratamiento) || Number(a.lote) - Number(b.lote)).map(record => categoryLabel(record, group)))];
  $('chart-subtitle').textContent = group === 'tratamiento'
    ? 'Distribución de valores entre parcelas de cada tratamiento; cada punto corresponde a una parcela.'
    : 'Una medición por parcela; los grupos con un solo valor no muestran dispersión.';
  const traces = [];
  for (const treatment of treatments) {
    const quantified = measured.filter(record => record.tratamiento === treatment);
    if (quantified.length) traces.push({
      type: 'box',
      name: treatmentName(treatment),
      x: quantified.map(record => categoryLabel(record, group)),
      y: quantified.map(record => Number(record.valor)),
      boxpoints: 'all', quartilemethod: 'linear', jitter: 0.28, pointpos: 0,
      customdata: quantified.map(record => [escapeHtml(record.resultado_original), parcelName(record), record.finca_id]),
      marker: { color: COLORS[treatment] },
      line: { color: COLORS[treatment] },
      hovertemplate: '%{customdata[1]}<br>Finca %{customdata[2]}<br>Resultado: %{customdata[0]} ' + unit + '<extra>%{fullData.name}</extra>'
    });
    const limited = censored.filter(record => record.tratamiento === treatment);
    if (limited.length) traces.push({
      type: 'scatter', mode: 'markers+text',
      name: `${treatmentName(treatment)} · límite reportado`,
      x: limited.map(record => categoryLabel(record, group)),
      y: limited.map(record => Number(record.limite_reportado)),
      text: limited.map(record => escapeHtml(record.resultado_original)),
      textposition: 'top center',
      customdata: limited.map(record => [parcelName(record), escapeHtml(record.operador), record.limite_reportado]),
      marker: {
        color: COLORS[treatment], size: 12,
        symbol: limited.map(record => record.operador.startsWith('>') ? 'triangle-up' : 'triangle-down'),
        line: { color: '#17251f', width: 1 }
      },
      hovertemplate: '%{customdata[0]}<br>Límite reportado: %{customdata[1]}%{customdata[2]} ' + unit +
        '<br>No representa una concentración medida<extra>%{fullData.name}</extra>'
    });
  }
  Plotly.react('chart', traces, {
    autosize: true, boxmode: 'group', paper_bgcolor: 'white', plot_bgcolor: 'white',
    font: { color: '#17251f' },
    yaxis: { title: `${cfg.vars[field][0]} (${unit})`, gridcolor: '#e5ece7' },
    xaxis: { title: $('group').selectedOptions[0].text, tickangle: -30, automargin: true,
      type: 'category', categoryorder: 'array', categoryarray: categories },
    margin: { t: 24, r: 24, b: 110, l: 75 },
    legend: { orientation: 'h', y: 1.12 }, showlegend: traces.length > 1,
    annotations: traces.length ? [] : [{ text: rows.length ? 'Sin valores numéricos ni límites reportados para mostrar.' : 'No hay datos para estos filtros.',
      x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', showarrow: false }]
  }, { responsive: true, displaylogo: false });
  $('rows').innerHTML = rows.map(record => {
    const result = record.resultado_original ? `${escapeHtml(record.resultado_original)} ${unit}` : '—';
    return `<tr><td>${treatmentName(record.tratamiento)}</td><td>${record.finca_id}</td>` +
      `<td>${treatmentName(record.tratamiento)} ${record.lote}</td><td>${result}</td></tr>`;
  }).join('') || '<tr><td colspan="4">No hay datos para estos filtros.</td></tr>';
}

async function loadAndRender() {
  const version = ++loadVersion;
  ready = false;
  $('results').hidden = true;
  $('load-error').hidden = true;
  $('retry').hidden = true;
  $('loading').hidden = false;
  $('chemical-note').hidden = true;
  $('dataset-label').hidden = currentModule !== 'physical';
  const controls = ['variable', 'group', 'treatment', 'farm', 'reset', 'download'];
  controls.forEach(id => { $(id).disabled = true; });
  try {
    if (!window.Plotly) throw new Error('No se pudo cargar la biblioteca de gráficos. Revisa la conexión y recarga la página.');
    await load(version);
    if (version !== loadVersion) return;
    ready = true;
    $('results').hidden = false;
    render();
    controls.forEach(id => { $(id).disabled = false; });
    $('load-error').hidden = true;
    $('coverage-rows').innerHTML = '<tr><td colspan="7">Cargando disponibilidad…</td></tr>';
    $('availability-warning').hidden = true;
    loadAvailability(version).catch(error => {
      if (version === loadVersion) $('coverage-rows').innerHTML = `<tr><td colspan="7">No se pudo consultar la disponibilidad: ${escapeHtml(error.message)}</td></tr>`;
    });
  } catch (error) {
    if (version !== loadVersion) return;
    ready = false;
    $('results').hidden = true;
    $('load-error').textContent = `No se pudieron cargar los datos: ${error.message}`;
    $('load-error').hidden = false;
    $('retry').hidden = location.protocol === 'file:';
    console.error(error);
  } finally {
    if (version === loadVersion) $('loading').hidden = true;
  }
}

['dataset', 'variable', 'group', 'treatment', 'farm'].forEach(id => {
  $(id).addEventListener('change', id === 'dataset' ? loadAndRender : render);
});
$('reset').onclick = () => {
  $('treatment').value = 'all';
  $('farm').value = 'all';
  render();
};
$('retry').onclick = loadAndRender;
$('download').onclick = () => Plotly.downloadImage('chart', {
  format: 'png', filename: 'comparacion-suelo', width: 1600, height: 900
});
$('dataset').innerHTML = Object.entries(configs)
  .map(([key, value]) => `<option value="${key}">${value.title}</option>`).join('');
$('back-home').onclick = () => {
  loadVersion += 1;
  ready = false;
  $('home').hidden = false;
  $('module-view').hidden = true;
  $('dashboard').hidden = true;
  $('chemical-note').hidden = true;
  document.querySelector('header p').textContent = 'Selecciona el tipo de análisis que quieres explorar.';
};
document.querySelectorAll('.module').forEach(button => {
  button.onclick = () => {
    const chemical = button.dataset.module === 'chemical';
    currentModule = chemical ? 'chemical' : 'physical';
    document.querySelector('header p').textContent = chemical
      ? 'Análisis químico · Compara las mediciones por parcela, tratamiento y finca.'
      : 'Análisis físico · Explora las repeticiones por parcela, tratamiento y finca.';
    $('home').hidden = true;
    $('module-view').hidden = false;
    $('dashboard').hidden = false;
    $('chemical-note').hidden = !chemical;
    $('group').value = 'tratamiento';
    loadAndRender();
  };
});
window.addEventListener('resize', () => {
  if (ready && !$('module-view').hidden) Plotly.Plots.resize('chart');
});


