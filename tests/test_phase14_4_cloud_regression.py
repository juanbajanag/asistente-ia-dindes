from pathlib import Path
import unittest

from src.corpus_builder import build_complete_corpus
from src.cloud_backend import CloudRAGPipeline

ROOT = Path(__file__).resolve().parents[1]


class TestPhase144CloudRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records = build_complete_corpus(ROOT / 'data', include_sample=True)
        cls.pipe = CloudRAGPipeline(
            dense_min_score=0.45,
            top_k=5,
            temperature=0.0,
        ).fit(records)

    def test_unknown_inventory_entity_does_not_count_everything(self):
        r = self.pipe.ask('¿Cuántos drones DJI Phantom 99 hay disponibles?')
        self.assertTrue(r.abstained)
        self.assertNotIn('66 registro', r.answer.lower())

    def test_creality_status_is_answered(self):
        r = self.pipe.ask('¿Cuál es el estado de la impresora Creality K1?')
        self.assertFalse(r.abstained)
        self.assertIn('operativo', r.answer.lower())

    def test_ai_inventory_components_are_answered(self):
        r = self.pipe.ask('¿Qué componentes del inventario pueden utilizarse para procesamiento de IA?')
        self.assertFalse(r.abstained)
        answer = r.answer.lower()
        self.assertTrue('rtx' in answer or 'jetson' in answer or 'alto rendimiento' in answer)

    def test_current_documents_are_answered(self):
        r = self.pipe.ask('¿Qué documentos se encuentran vigentes?')
        self.assertFalse(r.abstained)
        self.assertIn('vigente', r.answer.lower())
        self.assertGreaterEqual(r.retrieval_count, 1)

    def test_dewalt_stays_structured(self):
        r = self.pipe.ask('¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?')
        self.assertFalse(r.abstained)
        self.assertEqual(r.response_mode, 'structured')
        self.assertIn('1 unidad', r.answer.lower())

    def test_creality_quantity_still_works(self):
        r = self.pipe.ask('¿Cuántas impresoras 3D Creality K1 están disponibles?')
        self.assertFalse(r.abstained)
        self.assertIn('1 unidad', r.answer.lower())

    def test_unknown_document_still_abstains(self):
        r = self.pipe.ask('¿Cuál es el número de serie del generador principal de la fragata inexistente?')
        self.assertTrue(r.abstained)

    def test_empty_query_ui_clears_previous_response(self):
        app_text = (ROOT / 'app' / 'app.py').read_text(encoding='utf-8')
        start = app_text.index('if not question.strip():')
        snippet = app_text[start:start + 700]
        self.assertIn('st.session_state.last_response = None', snippet)
        self.assertIn('st.warning(', snippet)


if __name__ == '__main__':
    unittest.main()
