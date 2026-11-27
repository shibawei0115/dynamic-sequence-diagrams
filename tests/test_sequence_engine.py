import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sequence_engine import SequenceEngine

class TestSequenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SequenceEngine()
        self.engine.lifelines = [{"id": "A", "x": 0}, {"id": "B", "x": 0}]
        self.engine.messages = [{"id": "m1", "from": "A", "to": "B", "y": 0, "text": "getData"}]

    def test_auto_layout(self):
        self.engine.auto_layout()
        self.assertEqual(self.engine.lifelines[0]["x"], 120)
        self.assertEqual(self.engine.lifelines[1]["x"], 280)
        self.assertEqual(self.engine.messages[0]["y"], 100)

    def test_drag_and_persistence(self):
        self.engine.drag_lifeline("A", 350)
        self.assertEqual(self.engine.lifelines[1]["id"], "A")

        self.engine.drag_message("m1", 220)
        self.assertEqual(self.engine.messages[0]["y"], 220)

        self.engine.add_fragment("f1", "consider", 50, 50, 200, 100)
        self.engine.move_or_resize_fragment("f1", 60, 70, 250, 120)
        self.engine.edit_fragment_interactions("f1", ["getData", "processData"])

        test_file = "test_save_temp.json"
        self.engine.save_to_file(test_file)

        new_engine = SequenceEngine()
        self.assertTrue(new_engine.load_from_file(test_file))
        self.assertEqual(new_engine.lifelines[1]["id"], "A")
        self.assertEqual(new_engine.messages[0]["y"], 220)
        self.assertEqual(new_engine.fragments[0]["width"], 250)
        self.assertEqual(new_engine.fragments[0]["interactions"], ["getData", "processData"])

        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
