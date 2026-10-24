import unittest

from src.rag_pipeline import RAGPipeline


class FakeStructuredQuery:
    def __init__(
        self,
        brand=None,
        model=None,
        description_contains=None,
    ):
        self.brand = brand
        self.model = model
        self.description_contains = description_contains


class FakeStructuredEngine:
    def __init__(self, response):
        self.response = response

    def execute(self, question):
        return self.response

    def to_retrieval_results(self, records):
        return list(records)


class FakeRetriever:
    def __init__(self, results):
        self.results = list(results)

    def search(self, **kwargs):
        return list(self.results)


class FakeLLM:
    def __init__(self, answer):
        self.answer = answer

    def chat(self, **kwargs):
        return self.answer


class DummySource:
    """
    Objeto mínimo compatible con src/prompt_builder.py.
    """
    def __init__(
        self,
        *,
        record_id="INV-0008",
        title="Impresora 3D",
        source_type="inventory",
        text=(
            "Código: INV-0008. Descripción: Impresora 3D. "
            "Marca: Creality. Modelo: K1. Cantidad: 1. "
            "Estado: Operativo."
        ),
        metadata=None,
    ):
        self.record_id = record_id
        self.title = title
        self.source_type = source_type
        self.text = text
        self.metadata = metadata or {
            "categoria": "Fabricación digital",
            "estado": "Operativo",
            "ubicacion": "Taller Prototipado",
            "fecha_actualizacion": "2026-09-05",
        }


class TestLocalRAGFallback(unittest.TestCase):
    def _pipeline(
        self,
        structured_response,
        retrieval_results=None,
        llm_answer="Respuesta RAG [F1].",
    ):
        pipe = RAGPipeline.__new__(RAGPipeline)
        pipe._fitted = True
        pipe.top_k = 5
        pipe.dense_min_score = 0.45
        pipe.bm25_min_score = 0.01
        pipe.structured_engine = FakeStructuredEngine(
            structured_response
        )
        pipe.retriever = FakeRetriever(
            retrieval_results or []
        )
        pipe.llm = FakeLLM(llm_answer)
        return pipe

    def test_dewalt_keeps_structured_route_when_record_exists(self):
        structured = {
            "query": FakeStructuredQuery(
                brand="DEWALT",
                model="DWD024-B3",
            ),
            "records": [DummySource(
                record_id="DOC-REAL-002",
                title="Anexo D Inventario de bodega",
                text="Taladro DEWALT DWD024-B3. Stock: 1.",
            )],
            "answer": "El stock es 1 [F1].",
            "abstained": False,
            "structured_rows": [
                {"Modelo": "DWD024-B3", "Stock": "1"}
            ],
        }

        pipe = self._pipeline(structured)

        r = pipe.ask(
            "¿Cuál es el stock del taladro DEWALT "
            "modelo DWD024-B3?"
        )

        self.assertEqual(r.response_mode, "structured")
        self.assertFalse(r.abstained)
        self.assertEqual(len(r.structured_rows), 1)

    def test_missing_structured_entity_falls_back_to_rag(self):
        structured = {
            "query": FakeStructuredQuery(
                brand="CREALITY",
                model="K1",
            ),
            "records": [],
            "answer": (
                "No se encontró un registro estructurado "
                "que coincida con la consulta."
            ),
            "abstained": True,
            "structured_rows": [],
        }

        pipe = self._pipeline(
            structured,
            retrieval_results=[DummySource()],
            llm_answer=(
                "Hay 1 unidad(es) de Impresora 3D "
                "Creality K1 registradas en la evidencia "
                "disponible [F1]. Estado: Operativo."
            ),
        )

        r = pipe.ask(
            "¿Cuántas impresoras 3D Creality K1 "
            "están disponibles?"
        )

        self.assertEqual(r.response_mode, "rag")
        self.assertFalse(r.abstained)
        self.assertEqual(r.retrieval_count, 1)
        self.assertIn("1 unidad", r.answer)

    def test_structured_query_without_entity_filter_may_abstain_structured(self):
        structured = {
            "query": FakeStructuredQuery(),
            "records": [],
            "answer": "No se encontraron registros.",
            "abstained": True,
            "structured_rows": [],
        }

        pipe = self._pipeline(structured)

        r = pipe.ask(
            "¿Qué herramientas requieren reposición?"
        )

        self.assertEqual(r.response_mode, "structured")
        self.assertTrue(r.abstained)

    def test_unknown_document_query_still_abstains_at_retrieval(self):
        pipe = self._pipeline(
            None,
            retrieval_results=[],
        )

        r = pipe.ask(
            "¿Cuál es el número de serie del generador "
            "principal de la fragata inexistente?"
        )

        self.assertEqual(r.response_mode, "rag")
        self.assertTrue(r.abstained)
        self.assertEqual(
            r.abstention_stage,
            "retrieval",
        )


if __name__ == "__main__":
    unittest.main()
