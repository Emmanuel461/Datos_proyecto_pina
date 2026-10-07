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
const poxcVariables = {
  poxc: ['Carbono lábil (POXC)', 'mg POXC/kg de suelo seco']
};
const poxcConfig = {
  file: '../processed/poxc_analisis_listo/web/resultados_poxc.csv',
  title: 'Carbono lábil (POXC)', vars: poxcVariables
};
const poxcParcelFarms = {
  Bosque_1: '1', Pina_1: '1', Pina_2: '2', Pina_3: '3', Bosque_2: '3',
  Bosque_3: '4', Pina_4: '4', Bosque_4: '5', Pina_5: '5', Pina_6: '6',
  Pina_7: '7', Pina_8: '8'
};
const nematodeFamilies = {
  indicadores: 'Indicadores generales',
  parametros_muestra: 'Parámetros de conteo e identificación',
  indices_ninja: 'Índices NINJA',
  huellas_ninja: 'Biomasa, número y huellas NINJA',
  porcentajes_ninja: 'Porcentajes calculados por NINJA',
  grupos_abundancia: 'Abundancia por grupo alimenticio',
  grupos_composicion: 'Composición por grupo alimenticio',
  taxones_conteos: 'Conteos de identificación por taxón',
  taxones_abundancia: 'Abundancia por taxón',
  taxones_composicion: 'Composición porcentual por taxón'
};
const nematodeFamilySizes = {
  indicadores: 2,
  parametros_muestra: 5,
  indices_ninja: 8,
  huellas_ninja: 11,
  porcentajes_ninja: 26,
  grupos_abundancia: 5,
  grupos_composicion: 5,
  taxones_conteos: 35,
  taxones_abundancia: 35,
  taxones_composicion: 35
};
const nematodeConfig = {
  file: '../processed/nematodos_analisis_listo/web/resultados_nematodos.csv',
  title: 'Análisis de nematodos'
};
const nematodeTraitsFile = '../processed/nematodos_analisis_listo/web/rasgos_taxones.csv';

const COLORS = { Pina: '#bf801a', Bosque: '#24745b' };
let data = [];
let cfg;
let field;
let currentModule = 'physical';
let loadVersion = 0;
let ready = false;
let filteredExport = { columns: [], rows: [], filename: 'datos_filtrados.csv' };
const $ = id => document.getElementById(id);
const treatmentName = value => value === 'Pina' ? 'Pi\u00f1a' : value;
const parcelName = record => `${treatmentName(record.tratamiento)} ${record.lote}`;
const parcelContext = record => `Finca ${record.finca_id} · parcela ${parcelName(record)}`;
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
const isNumber = value => String(value).trim() !== '' && Number.isFinite(Number(value));

function csvCell(value) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`;
}

function exportFilename(...parts) {
  const stem = parts.join('_').normalize('NFKD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  return `${stem || 'datos_filtrados'}.csv`;
}

function setFilteredExport(columns, rows, filename) {
  filteredExport = { columns, rows, filename };
  $('download-csv').disabled = rows.length === 0;
}

function downloadFilteredCsv() {
  if (!filteredExport.rows.length) return;
  const lines = [filteredExport.columns, ...filteredExport.rows]
    .map(row => row.map(csvCell).join(','));
  const blob = new Blob([`\uFEFF${lines.join('\r\n')}\r\n`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filteredExport.filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

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
    const script = file.includes('nematodos_analisis_listo') ? '06_nematode_analysis.py'
      : file.includes('poxc_analisis_listo') ? '08_poxc_analysis.py'
        : file.includes('quimico_analisis_listo') ? '04_prepare_chemical_data.py' : '01_soil_data_pipeline.py';
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
      if (!Object.hasOwn(config.vars, record.variable) || record.unidad !== config.vars[record.variable][1]) {
        throw new Error(`${config.file}: variable o unidad de laboratorio no reconocida.`);
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
    const variables = Object.keys(config.vars);
    for (const parcel of assignments.keys()) {
      if (variables.some(variable => !seen.has(`${parcel}|${variable}`))) {
        throw new Error(`${config.file}: faltan registros de variables para ${parcel}.`);
      }
    }
  }
}

function validatePoxcData(records) {
  validateData(records, poxcConfig, false);
  if (records.length !== 12) {
    throw new Error(`${poxcConfig.file}: se esperaban 12 resultados y se encontraron ${records.length}.`);
  }
  const counts = { Pina: 0, Bosque: 0 };
  for (const record of records) {
    if (!Object.hasOwn(poxcParcelFarms, record.parcela) || poxcParcelFarms[record.parcela] !== record.finca_id) {
      throw new Error(`${poxcConfig.file}: la correspondencia de ${record.parcela} con la Finca ${record.finca_id} no es válida.`);
    }
    counts[record.tratamiento] += 1;
  }
  if (counts.Pina !== 8 || counts.Bosque !== 4) {
    throw new Error(`${poxcConfig.file}: se esperaban 8 parcelas de Piña y 4 de Bosque.`);
  }
}

function validateNematodeData(records, config = nematodeConfig) {
  const required = ['finca_id', 'tratamiento', 'lote', 'parcela', 'productor_finca',
    'familia', 'variable', 'etiqueta', 'unidad', 'valor', 'estado', 'detalle'];
  const seen = new Set();
  const definitions = new Map();
  const assignments = new Map();
  const variablesByParcel = new Map();
  for (const record of records) {
    if (required.some(column => !(column in record))) throw new Error(`${config.file}: faltan columnas requeridas.`);
    if (!Object.hasOwn(COLORS, record.tratamiento) || !/^[1-9]\d*$/.test(record.finca_id) ||
        !/^[1-9]\d*$/.test(record.lote) || record.parcela !== `${record.tratamiento}_${record.lote}` ||
        !Object.hasOwn(nematodeFamilies, record.familia) || !record.variable || !record.etiqueta || !record.unidad ||
        !['reportado', 'no_reportado'].includes(record.estado) ||
        (record.estado === 'reportado' ? !isNumber(record.valor) || Number(record.valor) < 0 : record.valor !== '')) {
      throw new Error(`${config.file}: resultado de nematodos inválido.`);
    }
    if (assignments.has(record.parcela) && assignments.get(record.parcela) !== record.finca_id) {
      throw new Error(`${config.file}: una parcela tiene varias fincas asignadas.`);
    }
    assignments.set(record.parcela, record.finca_id);
    const key = `${record.parcela}|${record.familia}|${record.variable}`;
    if (seen.has(key)) throw new Error(`${config.file}: resultado duplicado para ${key}.`);
    seen.add(key);
    if (!variablesByParcel.has(record.parcela)) variablesByParcel.set(record.parcela, new Set());
    variablesByParcel.get(record.parcela).add(`${record.familia}|${record.variable}`);
    const definition = `${record.etiqueta}|${record.unidad}`;
    const definitionKey = `${record.familia}|${record.variable}`;
    if (definitions.has(definitionKey) && definitions.get(definitionKey) !== definition) {
      throw new Error(`${config.file}: definición discordante para ${definitionKey}.`);
    }
    definitions.set(definitionKey, definition);
  }
  if (assignments.size !== 12) throw new Error(`${config.file}: se esperaban 12 parcelas y se encontraron ${assignments.size}.`);
  for (const [family, expected] of Object.entries(nematodeFamilySizes)) {
    const found = [...definitions.keys()].filter(key => key.startsWith(`${family}|`)).length;
    if (found !== expected) {
      throw new Error(`${config.file}: la familia ${family} contiene ${found} variables; se esperaban ${expected}.`);
    }
  }
  for (const [parcel, variables] of variablesByParcel) {
    if (variables.size !== definitions.size || [...definitions.keys()].some(key => !variables.has(key))) {
      throw new Error(`${config.file}: ${parcel} no contiene el conjunto completo de ${definitions.size} variables.`);
    }
  }
}

function validateNematodeTraits(records) {
  const required = ['taxon', 'grupo_alimenticio', 'grupo_resumido', 'clase_cp', 'clase_pp', 'masa_ug'];
  const seen = new Set();
  for (const record of records) {
    if (required.some(column => !(column in record)) || !record.taxon || !record.grupo_alimenticio ||
        !record.grupo_resumido || !isNumber(record.clase_cp) || !isNumber(record.clase_pp) ||
        !isNumber(record.masa_ug) || Number(record.masa_ug) < 0 || seen.has(record.taxon)) {
      throw new Error(`${nematodeTraitsFile}: catálogo de rasgos inválido.`);
    }
    seen.add(record.taxon);
  }
  if (seen.size !== 35) throw new Error(`${nematodeTraitsFile}: se esperaban 35 taxones y se encontraron ${seen.size}.`);
}

function fillNematodeTraits(records) {
  $('nematode-trait-rows').innerHTML = records.map(record =>
    `<tr><td>${escapeHtml(record.taxon)}</td><td>${escapeHtml(record.grupo_alimenticio)}</td>` +
    `<td>${escapeHtml(record.grupo_resumido)}</td><td>${escapeHtml(record.clase_cp)}</td>` +
    `<td>${escapeHtml(record.clase_pp)}</td><td>${Number(record.masa_ug).toFixed(3)}</td></tr>`
  ).join('');
}

function setDatasetOptions() {
  if (currentModule === 'physical') {
    $('dataset').innerHTML = Object.entries(configs)
      .map(([key, value]) => `<option value="${key}">${value.title}</option>`).join('');
  } else if (currentModule === 'nematodes') {
    $('dataset').innerHTML = Object.entries(nematodeFamilies)
      .map(([key, label]) => `<option value="${key}">${label}</option>`).join('');
  } else if (currentModule === 'poxc') {
    $('dataset').innerHTML = '<option value="poxc">Carbono lábil (POXC)</option>';
  } else {
    $('dataset').innerHTML = '<option value="chemical">Resultados químicos</option>';
  }
}

async function load(version) {
  const physical = currentModule === 'physical';
  const chemical = currentModule === 'chemical';
  const poxc = currentModule === 'poxc';
  const laboratory = chemical || poxc;
  const key = $('dataset').value;
  const nextConfig = physical ? configs[key]
    : chemical ? chemicalConfig : poxc ? poxcConfig : { ...nematodeConfig };
  const records = await readRecords(nextConfig.file);
  if (version !== loadVersion) return;
  if (currentModule === 'nematodes') {
    validateNematodeData(records, nextConfig);
    const traits = await readRecords(nematodeTraitsFile);
    if (version !== loadVersion) return;
    validateNematodeTraits(traits);
    fillNematodeTraits(traits);
    $('nematode-traits').hidden = false;
  } else {
    if (poxc) validatePoxcData(records);
    else validateData(records, nextConfig, physical);
    $('nematode-traits').hidden = true;
  }
  cfg = { ...nextConfig };
  data = currentModule === 'nematodes' ? records.filter(record => record.familia === key) : records;
  if (laboratory) {
    const available = new Set(data.map(record => record.variable));
    cfg.vars = Object.fromEntries(Object.entries(nextConfig.vars).filter(([variable]) => available.has(variable)));
  } else if (currentModule === 'nematodes') {
    cfg.title = nematodeFamilies[key];
    cfg.vars = {};
    for (const record of data) {
      if (Object.hasOwn(cfg.vars, record.variable)) {
        if (cfg.vars[record.variable][0] !== record.etiqueta || cfg.vars[record.variable][1] !== record.unidad) {
          throw new Error(`${cfg.file}: definición discordante para ${record.variable}.`);
        }
      } else {
        cfg.vars[record.variable] = [record.etiqueta, record.unidad];
      }
    }
  }
  if (!Object.keys(cfg.vars).length) throw new Error(`${cfg.file}: no hay variables disponibles.`);
  field = Object.keys(cfg.vars)[0];
  fillVars();
  fillViews();
  fillFilters();
  $('dataset-label').hidden = laboratory;
  $('variable-label').hidden = poxc;
  $('sample-heading').textContent = 'Repetición (R)';
  $('sample-heading').hidden = !physical;
  $('result-heading').textContent = 'Valor';
  $('n-label').textContent = physical ? 'Repeticiones con valor' : 'Parcelas visibles';
  $('mean-label').textContent = 'Media (promedio)';
  $('median-label').textContent = 'Mediana';
  $('range-label').textContent = 'Rango (mínimo–máximo)';
  $('analysis-note').hidden = physical;
  $('chart-subtitle').textContent = physical
    ? 'Cada punto representa una repetición (R) de una parcela en este análisis. Los resúmenes describen los datos filtrados.'
    : chemical ? 'Distribución de valores entre parcelas; cada punto corresponde a una muestra de laboratorio.'
      : poxc ? 'Un resultado final de POXC por parcela; las comparaciones mostradas son descriptivas.'
        : 'Distribución entre parcelas; cada punto corresponde a una muestra comunitaria de nematodos.';
  document.querySelector('footer').textContent = physical
    ? 'Fuente: tablas de processed/analisis_listo/; lectura de las columnas públicas en processed/analisis_listo/web/.'
    : chemical
      ? 'Fuente: processed/quimico_analisis_listo/resultados_quimicos.csv; lectura de las columnas públicas en processed/quimico_analisis_listo/web/. Fincas vinculadas mediante el diseño de muestreo.'
      : poxc
        ? 'Fuente: informe LAIMEC-042-2026; datos preparados por src/07_prepare_poxc_data.py y salida pública generada por src/08_poxc_analysis.py.'
        : 'Fuente: tablas validadas de processed/nematodos_analisis_listo/; resumen público generado por src/06_nematode_analysis.py.';
}

function fillVars() {
  $('variable').innerHTML = Object.entries(cfg.vars)
    .map(([key, value]) => `<option value="${key}">${value[0]}</option>`).join('');
  $('chart-title').textContent = cfg.title;
}

function fillViews() {
  $('view-label').hidden = currentModule !== 'nematodes';
  if (currentModule !== 'nematodes') {
    $('view').innerHTML = '<option value="variable">Vista por variable</option>';
    return;
  }
  const family = $('dataset').value;
  const options = [['variable', 'Variable individual']];
  if (family.startsWith('grupos_')) options.push(['stacked', 'Barras apiladas por parcela']);
  if (family.startsWith('taxones_')) options.push(['heatmap', 'Mapa de calor de todos los taxones']);
  if (['indicadores', 'indices_ninja', 'huellas_ninja', 'porcentajes_ninja'].includes(family)) {
    options.push(['paired', 'Comparación Piña–Bosque por finca']);
  }
  $('view').innerHTML = options.map(([value, label]) => `<option value="${value}">${label}</option>`).join('');
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
    { ...configs.densidad_porosidad, kind: 'physical' },
    { ...configs.retencion_humedad, kind: 'physical' },
    { ...configs.textural, kind: 'physical' },
    { ...chemicalConfig, kind: 'chemical' },
    { ...poxcConfig, kind: 'poxc' },
    { ...nematodeConfig, title: 'Nematodos', kind: 'nematodes' }
  ];
  // Cada tabla se lee por separado: no hay uniones ni comparaciones por R.
  const results = await Promise.allSettled(tables.map(async table => {
    const records = await readRecords(table.file);
    if (table.kind === 'nematodes') validateNematodeData(records, table);
    else if (table.kind === 'poxc') validatePoxcData(records);
    else validateData(records, table, table.kind === 'physical');
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
      if (table.kind !== 'nematodes') Object.entries(table.vars).forEach(([variable, [label]]) => {
        const missing = table.kind === 'physical'
          ? subset.filter(record => record[variable] === '').length
          : subset.filter(record => record.variable === variable && record.estado === 'faltante').length;
        if (missing) notes.push(table.kind === 'physical'
          ? `${table.title} · ${label}: ${missing} de ${subset.length} repeticiones sin valor reportado.`
          : `${table.title} · ${label}: sin valor reportado.`);
      });
      if (table.kind === 'physical') return `${subset.length} ${subset.length === 1 ? 'repetición' : 'repeticiones'}`;
      if (table.kind === 'nematodes') {
        const indicators = new Set(subset.filter(record => record.familia === 'indicadores').map(record => record.variable));
        return `1 muestra comunitaria<br>${indicators.size} indicadores generales`;
      }
      if (table.kind === 'poxc') return '1 resultado final<br>POXC cuantificado';
      // El formato químico tiene una fila por indicador, no por muestra.
      const reported = subset.filter(record => record.estado !== 'faltante').length;
      return `1 muestra de laboratorio<br>${reported} de ${Object.keys(table.vars).length} indicadores con resultado`;
    });
    const detail = notes.length ? notes.map(escapeHtml).join('<br>')
      : 'Sin valores faltantes en los análisis disponibles.';
    return `<tr><td>Finca ${parcel.finca}</td><td>${treatmentName(parcel.tratamiento)} ${parcel.lote}</td>` +
      counts.map(count => `<td>${count}</td>`).join('') + `<td>${detail}</td></tr>`;
  }).join('') || '<tr><td colspan="9">No se pudo consultar la disponibilidad de los análisis.</td></tr>';
}

function categoryLabel(record, group) {
  if (group === 'tratamiento') return treatmentName(record.tratamiento);
  if (group === 'finca_id') return `Finca ${record.finca_id}`;
  return parcelContext(record);
}

function render() {
  if (!ready) return;
  field = $('variable').value;
  $('result-heading').textContent = `Valor — ${cfg.vars[field][0]}`;
  if (currentModule === 'chemical' || currentModule === 'poxc') return renderLaboratory();
  if (currentModule === 'nematodes') return renderNematodes();
  const rows = data.filter(record =>
    ($('treatment').value === 'all' || record.tratamiento === $('treatment').value) &&
    ($('farm').value === 'all' || record.finca_id === $('farm').value) &&
    record[field] !== '' && record[field] != null && Number.isFinite(Number(record[field]))
  );
  const numbers = rows.map(record => Number(record[field]));
  const unit = cfg.vars[field][1];
  const label = cfg.vars[field][0];
  setFilteredExport(
    ['tratamiento', 'finca_id', 'parcela', 'repeticion', 'variable', 'etiqueta', 'valor', 'unidad'],
    rows.map(record => [
      treatmentName(record.tratamiento), record.finca_id, parcelName(record), record.repeticion,
      field, label, record[field], unit
    ]),
    exportFilename('fisico', $('dataset').value, field)
  );
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

function renderLaboratory() {
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
  const label = cfg.vars[field][0];
  setFilteredExport(
    ['tratamiento', 'finca_id', 'parcela', 'variable', 'etiqueta', 'resultado_original',
      'valor', 'operador', 'limite_reportado', 'estado', 'unidad'],
    rows.map(record => [
      treatmentName(record.tratamiento), record.finca_id, parcelName(record), record.variable, label,
      record.resultado_original, record.valor, record.operador, record.limite_reportado, record.estado, unit
    ]),
    exportFilename(currentModule === 'poxc' ? 'poxc' : 'quimico', field)
  );
  $('chart-title').textContent = cfg.vars[field][0];
  $('n').textContent = rows.length;
  $('n-note').textContent = `${measured.length} valores numéricos · ${censored.length} reportados como límite · ${missing.length} sin resultado`;
  $('mean').textContent = values.length
    ? `${(values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2)} ${unit}` : '—';
  $('median').textContent = median == null ? '—' : `${median.toFixed(2)} ${unit}`;
  $('range').textContent = sorted.length ? `${sorted[0].toFixed(2)} – ${sorted.at(-1).toFixed(2)} ${unit}` : '—';
  $('analysis-note').textContent = currentModule === 'poxc'
    ? 'El informe publica un resultado final de POXC por parcela. El triplicado pertenece al procedimiento analítico, ' +
      'pero sus valores individuales no fueron reportados y no se presentan como repeticiones R. ' +
      'Las muestras no disturbadas se vinculan con las parcelas de Bosque de la misma finca según el diseño de muestreo.'
    : 'El reporte químico actual tiene una muestra de laboratorio por parcela y no incluye repeticiones R. ' +
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

function filteredNematodeRows() {
  return data.filter(record =>
    ($('treatment').value === 'all' || record.tratamiento === $('treatment').value) &&
    ($('farm').value === 'all' || record.finca_id === $('farm').value)
  );
}

function renderNematodeStacked() {
  const rows = filteredNematodeRows().filter(record => record.estado === 'reportado' && isNumber(record.valor));
  const parcels = [...new Map([...rows].sort((a, b) => Number(a.finca_id) - Number(b.finca_id) ||
    a.tratamiento.localeCompare(b.tratamiento)).map(record => [record.parcela, record])).values()];
  const lookup = new Map(rows.map(record => [`${record.parcela}|${record.variable}`, Number(record.valor)]));
  const traces = Object.entries(cfg.vars).map(([variable, [label, unit]]) => ({
    type: 'bar', name: label,
    x: parcels.map(parcelContext),
    y: parcels.map(record => lookup.get(`${record.parcela}|${variable}`) ?? null),
    hovertemplate: '%{x}<br>%{y:.2f} ' + unit + '<extra>%{fullData.name}</extra>'
  }));
  $('chart-title').textContent = cfg.title;
  $('chart-subtitle').textContent = 'Todas las variables de esta familia, apiladas por parcela.';
  Plotly.react('chart', traces, {
    autosize: true, barmode: 'stack', paper_bgcolor: 'white', plot_bgcolor: 'white',
    font: { color: '#17251f' },
    yaxis: { title: Object.values(cfg.vars)[0][1], gridcolor: '#e5ece7' },
    xaxis: { title: 'Parcela', tickangle: -35, automargin: true },
    margin: { t: 24, r: 24, b: 130, l: 85 },
    legend: { orientation: 'h', y: 1.16 }
  }, { responsive: true, displaylogo: false });
}

function renderNematodeHeatmap() {
  const rows = filteredNematodeRows();
  const parcels = [...new Map([...rows].sort((a, b) => Number(a.finca_id) - Number(b.finca_id) ||
    a.tratamiento.localeCompare(b.tratamiento)).map(record => [record.parcela, record])).values()];
  const lookup = new Map(rows.map(record => [
    `${record.parcela}|${record.variable}`,
    record.estado === 'reportado' && isNumber(record.valor) ? Number(record.valor) : null
  ]));
  const variables = Object.keys(cfg.vars);
  const unit = Object.values(cfg.vars)[0][1];
  const trace = {
    type: 'heatmap',
    x: parcels.map(parcelContext),
    y: variables.map(variable => cfg.vars[variable][0]),
    z: variables.map(variable => parcels.map(record => lookup.get(`${record.parcela}|${variable}`) ?? null)),
    colorscale: 'YlGnBu', colorbar: { title: unit },
    hovertemplate: '%{x}<br>%{y}<br>%{z:.2f} ' + unit + '<extra></extra>'
  };
  $('chart-title').textContent = cfg.title;
  $('chart-subtitle').textContent = $('dataset').value === 'taxones_conteos'
    ? 'Todos los taxones y parcelas; las celdas vacías corresponden a conteos no reportados en la fuente.'
    : 'Todos los taxones y parcelas en una sola matriz de comparación.';
  Plotly.react('chart', [trace], {
    autosize: true, paper_bgcolor: 'white', plot_bgcolor: 'white', font: { color: '#17251f' },
    xaxis: { title: 'Parcela', tickangle: -35, automargin: true },
    yaxis: { title: 'Taxón', automargin: true },
    margin: { t: 24, r: 90, b: 140, l: 150 }
  }, { responsive: true, displaylogo: false });
}

function renderNematodePaired(rows, label, unit) {
  const byFarm = new Map();
  for (const record of rows) {
    if (!byFarm.has(record.finca_id)) byFarm.set(record.finca_id, new Map());
    byFarm.get(record.finca_id).set(record.tratamiento, record);
  }
  const pairs = [...byFarm.entries()].filter(([, treatments]) => treatments.has('Pina') && treatments.has('Bosque'))
    .sort((a, b) => Number(a[0]) - Number(b[0]));
  const traces = pairs.map(([farm, treatments]) => ({
    type: 'scatter', mode: 'lines+markers', name: `Finca ${farm}`,
    x: ['Bosque', 'Piña'],
    y: [Number(treatments.get('Bosque').valor), Number(treatments.get('Pina').valor)],
    customdata: [parcelContext(treatments.get('Bosque')), parcelContext(treatments.get('Pina'))],
    marker: { size: 10 }, line: { width: 2 },
    hovertemplate: '%{customdata}<br>%{y:.2f} ' + unit + '<extra>%{fullData.name}</extra>'
  }));
  $('chart-title').textContent = `${label} · comparación dentro de finca`;
  $('chart-subtitle').textContent = 'Cada línea une únicamente la parcela de Bosque y la de Piña pertenecientes a la misma finca.';
  Plotly.react('chart', traces, {
    autosize: true, paper_bgcolor: 'white', plot_bgcolor: 'white', font: { color: '#17251f' },
    yaxis: { title: `${label} (${unit})`, gridcolor: '#e5ece7' },
    xaxis: { title: 'Tratamiento', categoryorder: 'array', categoryarray: ['Bosque', 'Piña'] },
    margin: { t: 24, r: 24, b: 80, l: 90 },
    legend: { orientation: 'h', y: 1.14 },
    annotations: traces.length ? [] : [{ text: 'No hay pares Piña–Bosque con estos filtros.',
      x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', showarrow: false }]
  }, { responsive: true, displaylogo: false });
}

function renderNematodes() {
  field = $('variable').value;
  const selectedRows = data.filter(record =>
    record.variable === field &&
    ($('treatment').value === 'all' || record.tratamiento === $('treatment').value) &&
    ($('farm').value === 'all' || record.finca_id === $('farm').value)
  );
  const rows = selectedRows.filter(record => record.estado === 'reportado' && isNumber(record.valor));
  const values = rows.map(record => Number(record.valor)).filter(Number.isFinite);
  const sorted = [...values].sort((a, b) => a - b);
  const median = sorted.length
    ? sorted.length % 2 ? sorted[(sorted.length - 1) / 2]
      : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
    : null;
  const [label, unit] = cfg.vars[field];
  setFilteredExport(
    ['tratamiento', 'finca_id', 'parcela', 'familia', 'variable', 'etiqueta', 'valor',
      'estado', 'unidad', 'detalle'],
    selectedRows.map(record => [
      treatmentName(record.tratamiento), record.finca_id, parcelName(record), record.familia,
      record.variable, record.etiqueta, record.valor, record.estado, record.unidad, record.detalle
    ]),
    exportFilename('nematodos', $('dataset').value, field)
  );
  $('chart-title').textContent = label;
  $('result-heading').textContent = `Valor — ${label}`;
  $('n').textContent = selectedRows.length;
  $('n-note').textContent = `${rows.length} con valor · ${selectedRows.length - rows.length} no reportados · sin repeticiones R`;
  $('mean').textContent = values.length
    ? `${(values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2)} ${unit}` : '—';
  $('median').textContent = median == null ? '—' : `${median.toFixed(2)} ${unit}`;
  $('range').textContent = sorted.length ? `${sorted[0].toFixed(2)} – ${sorted.at(-1).toFixed(2)} ${unit}` : '—';
  $('analysis-note').textContent = 'Este análisis contiene una muestra comunitaria por parcela, sin repeticiones R. ' +
    'Las comparaciones mostradas son descriptivas. Las abundancias siguen la unidad indicada por la fuente ' +
    '(muestra de suelo de 100 cm³), y los índices provienen de NINJA.';
  $('rows').innerHTML = selectedRows.map(record =>
    `<tr><td>${treatmentName(record.tratamiento)}</td><td>${record.finca_id}</td>` +
    `<td>${treatmentName(record.tratamiento)} ${record.lote}</td>` +
    `<td>${record.estado === 'reportado' ? `${Number(record.valor).toFixed(2)} ${escapeHtml(unit)}` : 'No reportado'}</td></tr>`
  ).join('') || '<tr><td colspan="4">No hay datos para estos filtros.</td></tr>';

  if ($('view').value === 'stacked') return renderNematodeStacked();
  if ($('view').value === 'heatmap') return renderNematodeHeatmap();
  if ($('view').value === 'paired') return renderNematodePaired(rows, label, unit);

  const group = $('group').value;
  const treatments = [...new Set(rows.map(record => record.tratamiento))];
  const categories = [...new Set([...rows].sort((a, b) => Number(a.finca_id) - Number(b.finca_id) ||
    a.tratamiento.localeCompare(b.tratamiento) || Number(a.lote) - Number(b.lote)).map(record => categoryLabel(record, group)))];
  $('chart-subtitle').textContent = group === 'tratamiento'
    ? 'La caja resume la distribución entre parcelas de cada tratamiento; cada punto corresponde a una parcela.'
    : 'Comparación de valores individuales; cada marcador corresponde a una parcela.';
  const useBoxplot = group === 'tratamiento';
  const traces = treatments.map(treatment => {
    const subset = rows.filter(record => record.tratamiento === treatment);
    const trace = {
      type: useBoxplot ? 'box' : 'scatter', name: treatmentName(treatment),
      x: subset.map(record => categoryLabel(record, group)),
      y: subset.map(record => Number(record.valor)),
      customdata: subset.map(record => [parcelContext(record), record.detalle || '']),
      marker: { color: COLORS[treatment], size: useBoxplot ? 6 : 11 },
      line: { color: COLORS[treatment] },
      hovertemplate: '%{customdata[0]}<br>%{y} ' + unit +
        '<br>%{customdata[1]}<extra>%{fullData.name}</extra>'
    };
    if (useBoxplot) Object.assign(trace, {
      boxpoints: 'all', quartilemethod: 'linear', jitter: 0.28, pointpos: 0
    });
    else trace.mode = 'markers';
    return trace;
  });
  Plotly.react('chart', traces, {
    autosize: true, boxmode: 'group', paper_bgcolor: 'white', plot_bgcolor: 'white',
    font: { color: '#17251f' },
    yaxis: { title: `${label} (${unit})`, gridcolor: '#e5ece7' },
    xaxis: { title: $('group').selectedOptions[0].text, tickangle: -30, automargin: true,
      type: 'category', categoryorder: 'array', categoryarray: categories },
    margin: { t: 24, r: 24, b: 110, l: 85 },
    legend: { orientation: 'h', y: 1.12 }, showlegend: traces.length > 1,
    annotations: rows.length ? [] : [{ text: 'No hay datos para estos filtros.',
      x: 0.5, y: 0.5, xref: 'paper', yref: 'paper', showarrow: false }]
  }, { responsive: true, displaylogo: false });
}

async function loadAndRender() {
  const version = ++loadVersion;
  ready = false;
  $('results').hidden = true;
  $('load-error').hidden = true;
  $('retry').hidden = true;
  $('loading').hidden = false;
  $('analysis-note').hidden = true;
  $('nematode-traits').hidden = true;
  $('dataset-label').hidden = currentModule === 'chemical' || currentModule === 'poxc';
  $('variable-label').hidden = currentModule === 'poxc';
  const controls = ['variable', 'view', 'group', 'treatment', 'farm', 'reset', 'download', 'download-csv'];
  controls.forEach(id => { $(id).disabled = true; });
  try {
    if (!window.Plotly) throw new Error('No se pudo cargar la biblioteca de gráficos. Revisa la conexión y recarga la página.');
    await load(version);
    if (version !== loadVersion) return;
    ready = true;
    $('results').hidden = false;
    render();
    controls.forEach(id => { $(id).disabled = false; });
    $('download-csv').disabled = filteredExport.rows.length === 0;
    $('load-error').hidden = true;
    $('coverage-rows').innerHTML = '<tr><td colspan="9">Cargando disponibilidad…</td></tr>';
    $('availability-warning').hidden = true;
    loadAvailability(version).catch(error => {
      if (version === loadVersion) $('coverage-rows').innerHTML = `<tr><td colspan="9">No se pudo consultar la disponibilidad: ${escapeHtml(error.message)}</td></tr>`;
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

['dataset', 'variable', 'view', 'group', 'treatment', 'farm'].forEach(id => {
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
$('download-csv').onclick = downloadFilteredCsv;
setDatasetOptions();
$('back-home').onclick = () => {
  loadVersion += 1;
  ready = false;
  $('home').hidden = false;
  $('module-view').hidden = true;
  $('dashboard').hidden = true;
  $('analysis-note').hidden = true;
  $('nematode-traits').hidden = true;
  document.querySelector('header p').textContent = 'Selecciona el tipo de análisis que quieres explorar.';
};
document.querySelectorAll('.module').forEach(button => {
  button.onclick = () => {
    currentModule = button.dataset.module;
    const messages = {
      physical: 'Análisis físico · Explora las repeticiones por parcela, tratamiento y finca.',
      chemical: 'Análisis químico · Compara las mediciones por parcela, tratamiento y finca.',
      nematodes: 'Nematodos · Explora abundancias, grupos alimenticios e índices por parcela.',
      poxc: 'Carbono lábil (POXC) · Compara un resultado final por parcela, tratamiento y finca.'
    };
    document.querySelector('header p').textContent = messages[currentModule];
    $('sampling-note').innerHTML = currentModule === 'physical'
      ? '<strong>R significa repetición:</strong> R1 es la repetición 1, R2 es la repetición 2, etc. Estas repeticiones son submuestras de una parcela dentro de cada análisis; R1 de densidad no se empareja con R1 de textura.'
      : currentModule === 'chemical'
        ? '<strong>Una muestra por parcela:</strong> el reporte químico no contiene repeticiones R y sus indicadores no se emparejan con las repeticiones físicas.'
        : currentModule === 'poxc'
          ? '<strong>Un resultado final por parcela:</strong> el triplicado fue parte del procedimiento analítico, pero el informe no publica sus valores individuales y no se crean repeticiones R. Las muestras no disturbadas corresponden a las parcelas de Bosque de la misma finca según el diseño de muestreo.'
          : '<strong>Una muestra comunitaria por parcela:</strong> este análisis no contiene repeticiones R ni se empareja con las repeticiones físicas. El número de parcela no es el número de finca; por ejemplo, la parcela Bosque 2 pertenece a la Finca 3 según el diseño de muestreo.';
    setDatasetOptions();
    $('home').hidden = true;
    $('module-view').hidden = false;
    $('dashboard').hidden = false;
    $('analysis-note').hidden = currentModule === 'physical';
    $('group').value = 'tratamiento';
    loadAndRender();
  };
});
window.addEventListener('resize', () => {
  if (ready && !$('module-view').hidden) Plotly.Plots.resize('chart');
});


