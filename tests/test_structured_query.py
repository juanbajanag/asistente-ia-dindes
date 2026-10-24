import unittest

from src.structured_query import StructuredQueryRouter


class TestStructuredQuery(unittest.TestCase):
    def test_stock_query_is_detected(self):
        q = StructuredQueryRouter.infer(
            "¿Cuál es el stock del taladro DEWALT modelo DWD024-B3?"
        )
        self.assertTrue(q.matched)
        self.assertEqual(q.brand, "DEWALT")
        self.assertEqual(q.model, "DWD024-B3")

    def test_document_question_is_not_forced_to_inventory(self):
        q = StructuredQueryRouter.infer(
            "¿Qué componentes principales integra la arquitectura del Simulador Táctico Submarino?"
        )
        self.assertFalse(q.matched)


if __name__ == "__main__":
    unittest.main()
