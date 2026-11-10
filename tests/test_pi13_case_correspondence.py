"""Cross-document checks for PI12 identifiers and the PI13 execution ledger."""
import csv
import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
PI13 = ROOT / 'docs/evidencias/pi13'


def read_csv(name):
    with (PI13 / name).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def test_original_pi12_case_ids_and_scenarios_are_preserved_in_registry():
    plan = Document(ROOT / 'docs/evidencias/T5-T9_PI11-PI12.docx')
    table = next(t for t in plan.tables if t.cell(0, 0).text == 'Caso')
    original = {r.cells[0].text: r.cells[1].text for r in table.rows[1:13]}
    canonical = {r['id']: r['escenario'] for r in read_csv('casos-canonicos.csv')}
    assert set(original) == {f'CP{i:02}' for i in range(1, 13)}
    assert all(canonical[case] == scenario for case, scenario in original.items())


def test_execution_ledger_separates_execution_from_acceptance_without_promoting_unrun_cases():
    registry = {r['id']: r for r in read_csv('casos-canonicos.csv')}
    rows = read_csv('cp-ejecucion.csv')
    assert len({r['id'] for r in rows}) == len(rows)
    assert {r['id'] for r in rows} == set(registry)
    for row in rows:
        assert row['escenario'] == registry[row['id']]['escenario']
        assert row['estado_ejecucion'] in {'Ejecutado', 'Bloqueado', 'No ejecutado'}
        assert row['cumple'] in {'Sí', 'No', 'Parcial', 'No verificado'}
        if row['estado_ejecucion'] == 'No ejecutado':
            assert int(row['n_ejecuciones']) == 0
            assert row['cumple'] == 'No verificado'


def test_previous_execution_metadata_remains_traceable_after_remapping():
    old = {r['id']: r for r in read_csv('historico/cp-ejecucion-antes-correspondencia.csv')}
    equivalences = {(r['id_anterior_pi13'], r['id_canonico']) for r in read_csv('correspondencia-casos.csv')}
    for row in read_csv('cp-ejecucion.csv'):
        previous = row['id_anterior_pi13']
        if previous not in old:
            continue
        assert (previous, row['id']) in equivalences
        assert row['fecha'] == old[previous]['fecha']
        assert row['ejecutor'] == old[previous]['ejecutor']
        assert row['n_ejecuciones'] == old[previous]['N° ejecuciones']


def test_traceability_references_existing_cases_and_real_test_functions():
    registry = {r['id'] for r in read_csv('casos-canonicos.csv')}
    for row in read_csv('trazabilidad.csv'):
        assert set(re.findall(r'CP\d+', row['CP'])) <= registry
        reference = row['evidencia']
        path, _, function = reference.partition('::')
        source = ROOT / path
        if not source.exists():
            assert row['estado'] == 'No verificado'
        elif function:
            assert re.search(r'^def ' + re.escape(function) + r'\(', source.read_text(), re.M)
