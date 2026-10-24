from types import SimpleNamespace
import unittest

from src.abstention_guard import (
    contains_abstention_marker,
    substantive_score,
    is_mixed_generation_abstention,
)


class TestAbstentionGuard(unittest.TestCase):
    def test_marker_detection(self):
        self.assertTrue(
            contains_abstention_marker(
                "No se encontró evidencia suficiente en las fuentes disponibles."
            )
        )

    def test_pure_abstention_is_not_mixed(self):
        response = SimpleNamespace(
            abstained=True,
            abstention_stage="generation",
            answer="No se encontró evidencia suficiente en las fuentes disponibles.",
        )
        self.assertFalse(is_mixed_generation_abstention(response))

    def test_substantive_score_counts_citations(self):
        info = substantive_score(
            "El sistema integra estaciones de instructor y módulos de simulación [F1]."
        )
        self.assertEqual(info["citation_count"], 1)


if __name__ == "__main__":
    unittest.main()
