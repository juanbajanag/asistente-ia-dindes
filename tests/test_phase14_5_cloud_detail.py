from pathlib import Path
import unittest
from src.corpus_builder import build_complete_corpus
from src.cloud_backend import CloudRAGPipeline

ROOT = Path(__file__).resolve().parents[1]

class TestPhase145CloudDetail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipe = CloudRAGPipeline(
            dense_min_score=0.45, top_k=5, temperature=0.0
        ).fit(build_complete_corpus(ROOT / "data", include_sample=True))

    def test_model_detail_is_richer(self):
        r = self.pipe.ask("¿Qué información existe del modelo DWD024-B3?")
        self.assertFalse(r.abstained)
        a = r.answer.lower()
        self.assertIn("dwd024-b3", a)
        self.assertTrue(any(x in a for x in (
            "descripción", "descripcion", "marca", "stock", "cantidad", "modelo"
        )))

    def test_identifier_detail_if_code_exists(self):
        r = self.pipe.ask(
            "¿Qué información consta en el documento Bienes DINDES para el bien código 2341766?"
        )
        if not r.abstained:
            a = r.answer.lower()
            self.assertIn("2341766", a)
            self.assertTrue(any(x in a for x in (
                "título:", "descripción:", "marca:", "modelo:",
                "cantidad:", "stock:", "estado:", "ubicación:", "evidencia:"
            )))

    def test_dewalt_stock_unchanged(self):
        r = self.pipe.ask("¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?")
        self.assertFalse(r.abstained)
        self.assertEqual(r.response_mode, "structured")
        self.assertIn("1 unidad", r.answer.lower())

    def test_dji_unknown_still_abstains(self):
        self.assertTrue(
            self.pipe.ask("¿Cuántos drones DJI Phantom 99 hay disponibles?").abstained
        )

    def test_unknown_document_still_abstains(self):
        self.assertTrue(
            self.pipe.ask(
                "¿Cuál es el número de serie del generador principal de la fragata inexistente?"
            ).abstained
        )

if __name__ == "__main__":
    unittest.main()
