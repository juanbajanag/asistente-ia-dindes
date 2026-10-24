from pathlib import Path
import unittest

from src.corpus_builder import build_complete_corpus
from src.cloud_backend import CloudRAGPipeline

ROOT = Path(__file__).resolve().parents[1]


class TestCloudBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records = build_complete_corpus(ROOT / "data", include_sample=True)
        cls.pipe = CloudRAGPipeline(
            dense_min_score=0.45,
            top_k=5,
            temperature=0.0,
        ).fit(records)

    def test_document_rag(self):
        r = self.pipe.ask(
            "¿Qué componentes principales integra la arquitectura del Simulador Táctico Submarino?"
        )
        self.assertEqual(r.response_mode, "rag")
        self.assertFalse(r.abstained)
        self.assertGreaterEqual(r.retrieval_count, 1)

    def test_quantitative_sample_inventory(self):
        r = self.pipe.ask(
            "¿Cuántas impresoras 3D Creality K1 están disponibles?"
        )
        self.assertFalse(r.abstained)
        self.assertIn("1 unidad(es)", r.answer)

    def test_unknown_question_abstains(self):
        r = self.pipe.ask(
            "¿Cuál es el número de serie del generador principal de la fragata inexistente?"
        )
        self.assertTrue(r.abstained)
        self.assertEqual(r.abstention_stage, "retrieval")


if __name__ == "__main__":
    unittest.main()
