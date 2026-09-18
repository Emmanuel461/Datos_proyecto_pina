import importlib.util
import unittest
from pathlib import Path

import pandas as pd

# Orden de ejecucion: 02
# Valida la limpieza real: columnas relevantes, orden de hojas y normalizacion.

module_path = Path(__file__).resolve().parent / '01_soil_data_pipeline.py'
spec = importlib.util.spec_from_file_location('soil_data_pipeline', module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PHYSICAL_SHEETS = module.PHYSICAL_SHEETS
select_relevant_columns = module.select_relevant_columns
normalize_text = module.normalize_text


class SoilPhysicalPipelineTests(unittest.TestCase):
    def test_short_id_rep_is_not_a_producer(self):
        parsed = module.parse_id_usuario('PIÑA 1-8')
        self.assertEqual(parsed['tratamiento'], 'Pina')
        self.assertEqual(parsed['lote'], '1')
        self.assertEqual(parsed['repeticion'], '8')
        self.assertEqual(parsed['productor'], '')
        self.assertEqual(parsed['id_usuario_normalizado'], 'Pina 1 R8')

    def test_explicit_rep_with_producer(self):
        for identifier in ['BOSQUE 2 MISAEL ROJAS R1', 'BOSQUE 2 MISAEL ROJAS R 1']:
            with self.subTest(identifier=identifier):
                parsed = module.parse_id_usuario(identifier)
                self.assertEqual(parsed['repeticion'], '1')
                self.assertEqual(parsed['productor'], 'MISAEL ROJAS')
                self.assertEqual(parsed['tratamiento'], 'Bosque')

    def test_unknown_id_is_not_assigned_to_pina(self):
        parsed = module.parse_id_usuario('Muestra desconocida 1')
        self.assertEqual(parsed['tratamiento'], '')
        self.assertEqual(parsed['lote'], '')

    def test_column_normalization(self):
        self.assertEqual(normalize_text('Piña 1-1'), 'Pina 1-1')
        self.assertEqual(normalize_text('Densidad aparente (g cm-3)'), 'Densidad aparente g cm-3')

    def test_build_analysis_table_for_density_sheet(self):
        raw = pd.DataFrame([
            ['PIÑA 1-1', 'RN-26-00425', 0.77, 2.58, 70.15, '98535 ...'],
        ], columns=['ID USUARIO', 'ID LAB', 'Densidad aparente (g cm-3)', 'Densidad Particulas (g cm-3)', 'Porosidad (%)', 'xls_origen'])
        table = module.build_analysis_table(raw, 'densidad_porosidad')
        self.assertEqual(
            list(table.columns),
            ['id_usuario', 'id_lab', 'densidad_aparente_g_cm_3', 'densidad_particulas_g_cm_3', 'porosidad', 'xls_origen',
             'id_usuario_normalizado', 'zona', 'tratamiento', 'lote', 'repeticion', 'productor']
        )
        self.assertEqual(table.iloc[0, 0], 'Pina 1-1')
        self.assertEqual(table.iloc[0]['repeticion'], '1')

    def test_duplicate_lab_results_conserve_sources(self):
        df = pd.DataFrame({'id_lab': ['A', 'A', 'B'], 'xls_origen': ['uno', 'dos', 'uno'],
                           'valor': [5.0, 5.0, 7.0]})
        unique, duplicates = module.consolidate_lab_duplicates(df)
        self.assertEqual(len(unique), 2)
        self.assertEqual(len(duplicates), 2)
        self.assertEqual(unique.loc[unique['id_lab'].eq('A'), 'xls_origen'].iloc[0], 'dos | uno')

    def test_discordant_duplicates_stop_preparation(self):
        df = pd.DataFrame({'id_lab': ['A', 'A'], 'xls_origen': ['uno', 'dos'], 'valor': [5.0, 6.0]})
        with self.assertRaisesRegex(ValueError, 'discordantes'):
            module.consolidate_lab_duplicates(df)

    def test_actual_field_map_uses_finca_not_equal_lot_numbers(self):
        path = module_path.parent.parent / 'raw' / 'pina' / 'PIÑA FINCAS PRODUCTORAS .xlsx'
        design = module.read_field_design(path)
        bosque = design.loc[design['tratamiento'].eq('Bosque')].set_index('lote')
        self.assertEqual(bosque['finca_id'].to_dict(), {'1': 1, '2': 3, '3': 4, '4': 5})
        self.assertEqual(len(design), 12)
        self.assertNotIn('telefono', design.columns)
        self.assertNotIn('cedula', design.columns)

    def test_productor_ficha_is_not_duplicated_across_uses_in_same_finca(self):
        path = module_path.parent.parent / 'raw' / 'pina' / 'PIÑA FINCAS PRODUCTORAS .xlsx'
        design = module.read_field_design(path)

        finca_1_bosque = design.loc[(design['finca_id'].eq(1)) & (design['tratamiento'].eq('Bosque')) & (design['lote'].eq('1'))]
        self.assertEqual(len(finca_1_bosque), 1)
        self.assertEqual(finca_1_bosque['productor_ficha'].iloc[0], '')

        finca_1_pina = design.loc[(design['finca_id'].eq(1)) & (design['tratamiento'].eq('Pina')) & (design['lote'].eq('1'))]
        self.assertEqual(finca_1_pina['productor_ficha'].iloc[0], 'Victor Trejos Sanchez')


if __name__ == '__main__':
    unittest.main()
