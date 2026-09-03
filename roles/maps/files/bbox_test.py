import unittest
tile_extract = __import__("tile-extract")

class TestOverlap(unittest.TestCase):
    def test_split_antimeridian_bbox(self):
        self.assertEqual(tile_extract._split_antimeridian_bbox([170, 80, -170, 90]), ([170, 80, 180, 90], [-180, 80, -170, 90]))

    def test_overlap_neither_antimeridian_cross(self):
        """
        Test overlaps and non-overlaps between two regions, neither of which cross the antimeridian
        """

        self.assertTrue(tile_extract._has_overlap([0, 0, 20, 20], [10, 10, 30, 30]), "expected: regions overlap")

        self.assertFalse(tile_extract._has_overlap([0, 0, 20, 20], [30, 30, 40, 40]), "expected: no overlap - disjoint lat and lon")
        self.assertFalse(tile_extract._has_overlap([0, 0, 20, 20], [10, 30, 30, 40]), "expected: no overlap - disjoint only lat")
        self.assertFalse(tile_extract._has_overlap([0, 0, 20, 20], [30, 10, 40, 30]), "expected: no overlap - disjoint only lon")

        self.assertFalse(tile_extract._has_overlap([0, 0, 20, 20], [20, 0, 40, 20]), "expected: no overlap - borders on lon")
        self.assertFalse(tile_extract._has_overlap([0, 0, 20, 20], [0, 20, 20, 40]), "expected: no overlap - borders on lat")

    def test_overlap_one_antimeridian_cross(self):
        """
        Test overlaps and non-overlaps between two regions, one of which crosses the antimeridian
        """

        self.assertTrue(tile_extract._has_overlap([160, 0, -160, 20], [-170, 0, -150, 20]), "expected: overlap - east of antimeridian (-170 to -160)")
        self.assertTrue(tile_extract._has_overlap([160, 0, -160, 20], [150, 0, 170, 20]), "expected: overlap - west of antimeridian (160 to 170)")

        self.assertFalse(tile_extract._has_overlap([160, 0, -160, 20], [-150, 0, -140, 20]), "expected: no overlap - east of antimeridian")
        self.assertFalse(tile_extract._has_overlap([160, 0, -160, 20], [140, 0, 150, 20]), "expected: no overlap - west of antimeridian")

    def test_overlap_both_antimeridian_cross(self):
        """
        Test overlaps and non-overlaps between two antimeridian-crossing regions
        """

        self.assertTrue(tile_extract._has_overlap([160, 0, -160, 20], [170, 0, -150, 20]), "expected: overlap - first region starts and ends more east than second region does")
        self.assertTrue(tile_extract._has_overlap([160, 0, -160, 20], [150, 0, -170, 20]), "expected: overlap - first region starts and ends more west than second region does")
        self.assertTrue(tile_extract._has_overlap([160, 0, -160, 20], [170, 0, -170, 20]), "expected: overlap - first region fully contains second region")
        self.assertTrue(tile_extract._has_overlap([170, 0, -170, 20], [160, 0, -160, 20]), "expected: overlap - second region fully contains first region")

if __name__ == "__main__":
    unittest.main()
