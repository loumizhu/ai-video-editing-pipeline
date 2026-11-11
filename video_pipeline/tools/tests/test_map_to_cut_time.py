#!/usr/bin/env python3
"""test_map_to_cut_time.py - Selftest for map_to_cut_time.py tool."""

import json
import os
import sys
import tempfile
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import map_to_cut_time


class TestMapToCutTime(unittest.TestCase):

    def setUp(self):
        # 3 segments cut test data at 24 fps
        self.cuts_data = {
            "fps_num": 24000,
            "fps_den": 1000,
            "fps": "24/1",
            "segments": [
                {
                    "cut_index": 1,
                    "start": 1.0,
                    "end": 5.0,
                    "dur_frames": 96,
                    "dur_s": 4.0,
                    "note": "Seg 1",
                },
                {
                    "cut_index": 2,
                    "start": 10.0,
                    "end": 20.0,
                    "dur_frames": 240,
                    "dur_s": 10.0,
                    "note": "Seg 2",
                },
                {
                    "cut_index": 3,
                    "start": 30.0,
                    "end": 35.0,
                    "dur_frames": 120,
                    "dur_s": 5.0,
                    "note": "Seg 3",
                },
            ],
        }

    def test_anchor_in_first_segment(self):
        res = map_to_cut_time.map_source_time_to_cut(self.cuts_data, 2.0)
        self.assertEqual(res["cut_index"], 1)
        self.assertAlmostEqual(res["timeline_time_s"], 1.0)
        self.assertEqual(res["timeline_frame"], 24)
        self.assertEqual(res["resolve_record_frame"], 86400 + 24)
        self.assertEqual(res["timeline_ticks"], 254016000000)

    def test_anchor_in_second_segment(self):
        # 12.0s is 2.0s into segment 2 (which starts at 10.0s).
        # Preceding duration = 4.0s (96 frames).
        # Expected timeline_time_s = 4.0 + 2.0 = 6.0s (frame 96 + 48 = 144).
        res = map_to_cut_time.map_source_time_to_cut(self.cuts_data, 12.0)
        self.assertEqual(res["cut_index"], 2)
        self.assertAlmostEqual(res["timeline_time_s"], 6.0)
        self.assertEqual(res["timeline_frame"], 144)
        self.assertEqual(res["resolve_record_frame"], 86400 + 144)

    def test_anchor_in_removed_region_raises(self):
        # 7.0s is between 5.0s and 10.0s (removed cut material)
        with self.assertRaises(ValueError) as ctx:
            map_to_cut_time.map_source_time_to_cut(self.cuts_data, 7.0)
        self.assertIn("falls inside removed cut material", str(ctx.exception))

    def test_anchor_before_start_raises(self):
        # 0.5s is before segment 1 start (1.0s)
        with self.assertRaises(ValueError):
            map_to_cut_time.map_source_time_to_cut(self.cuts_data, 0.5)

    def test_list_words(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"words": [{"word": "hello", "start": 0.0, "end": 0.5}, {"word": "world", "start": 0.5, "end": 1.0}]}, f)
            w_path = f.name
        try:
            count = map_to_cut_time.list_words(w_path)
            self.assertEqual(count, 2)
        finally:
            os.remove(w_path)


if __name__ == "__main__":
    unittest.main()
