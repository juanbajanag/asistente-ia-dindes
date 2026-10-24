from pathlib import Path
import unittest

from src.data_processing import (
    load_document_dataset,
    load_inventory_dataset,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class TestDataProcessing(unittest.TestCase):
    def test_document_dataset_loads(self):
        records = load_document_dataset(
            DATA / "Dataset_1_Documentacion_Tecnica_DINDES_Sample.csv"
        )
        self.assertEqual(len(records), 8)
        self.assertTrue(all(r.source_type == "document" for r in records))
        self.assertTrue(all(r.record_id for r in records))

    def test_inventory_dataset_loads(self):
        records = load_inventory_dataset(
            DATA / "Dataset_2_Inventario_Institucional_DINDES_Sample.csv"
        )
        self.assertEqual(len(records), 10)
        self.assertTrue(all(r.source_type == "inventory" for r in records))
        self.assertTrue(any(r.metadata.get("modelo") == "K1" for r in records))


if __name__ == "__main__":
    unittest.main()
