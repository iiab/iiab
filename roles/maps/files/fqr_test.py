import unittest
from fqr import FQR

class TestFQR(unittest.TestCase):
    MIN_ALLOWED_LON = -179.99999999999997

class TestConvertFrom(TestFQR):
    def test_const(self):
        """
        Confirm, for the sake of other tests, that `MIN_ALLOWED_LON`
        (179.99999999999997) is the lowest value above -180.
        """
        # It seems that 179.99999999999997 is the lowest value that Python's normal number
        # type considers to be greater than -180. Experimentally, any number
        # between -179.99999999999997 and -180 seems to round to one or the other.
        self.assertEqual(-179.99999999999997, self.MIN_ALLOWED_LON)
        self.assertEqual(-179.99999999999998, self.MIN_ALLOWED_LON)
        self.assertEqual(-179.99999999999999, -180)

    def test_init_fqr(self):
        """
        Test that there's no problem creating a basic FQR
        """
        fqr = FQR([0, 10, 50, 60])
        self.assertEqual(fqr.min_lon, 0)
        self.assertEqual(fqr.min_lat, 10)
        self.assertEqual(fqr.max_lon, 50)
        self.assertEqual(fqr.max_lat, 60)

    def test_init_fqr_errors(self):
        def try_bad_bbox(bbox, exc, msg):
            with self.assertRaises(exc) as cm:
                FQR(bbox)
            self.assertEqual(str(cm.exception), msg)

        try_bad_bbox("10,20,30,40", TypeError, "bbox is not an array")
        try_bad_bbox([], ValueError, "bbox has unexpected length")
        try_bad_bbox([10, "20", 30, 40], TypeError, "coordinate is not a number")

        # lon either order no problem
        FQR([10, 20, 30, 40])
        FQR([10, 20, 5, 40])
        try_bad_bbox([10, 20, 10, 40], ValueError, "longitudes are equal")

        FQR([10, 20, 180, 40]) # lon 180 no problem
        try_bad_bbox([10, 20, 180.01, 40], ValueError, "longitude > 180")
        FQR([10, 20, self.MIN_ALLOWED_LON, 40]) # lon almost -180 no problem
        try_bad_bbox([10, 20, -180, 40], ValueError, f"longitude <= -180")

        try_bad_bbox([10, 20, 30, 20], ValueError, "latitudes are equal or out of order")
        try_bad_bbox([10, 20, 30, 19], ValueError, "latitudes are equal or out of order")
        FQR([10, 20, 30, 90]) # lat 90 no problem
        try_bad_bbox([10, 20, 30, 90.001], ValueError, "latitude > 90")
        FQR([10, -90, 30, 10]) # lat -90 no problem
        try_bad_bbox([10, -90.001, 30, 10], ValueError, "latitude < -90")

    def test_from_bbox_str(self):
        """
        Test that there's no problem creating a basic FQR from string
        """
        fqr = FQR.from_bbox_str("0,10,50,60")
        self.assertEqual(fqr.min_lon, 0)
        self.assertEqual(fqr.min_lat, 10)
        self.assertEqual(fqr.max_lon, 50)
        self.assertEqual(fqr.max_lat, 60)

    def test_from_bbox_str_errors(self):
        def try_bad_bbox_str(bbox_str, exc, msg):
            with self.assertRaises(exc) as cm:
                FQR.from_bbox_str(bbox_str)
            self.assertEqual(str(cm.exception), msg)

        try_bad_bbox_str("10,o,30,40", ValueError, "bbox (10,o,30,40) is malformed: could not convert string to float: 'o'")
        try_bad_bbox_str("10,20,30,100", ValueError, "bbox ([10.0, 20.0, 30.0, 100.0]) is invalid: latitude > 90")

class TestConvertTo(TestFQR):
    def test_to_bbox(self):
        bbox = [0, 10, 50, 60]
        self.assertEqual(FQR(bbox).to_bbox(), bbox)

    def test_to_bbox_str(self):
        bbox = [0, 10, 50.5, 60.5]
        self.assertEqual(FQR(bbox).to_bbox_str(), "0,10,50.5,60.5")

class TestOverlap(TestFQR):

    def test_crosses_antimeridian(self):
        self.assertTrue(FQR([170, 80, -170, 90]).crosses_antimeridian())
        self.assertFalse(FQR([-170, 80, 170, 90]).crosses_antimeridian())

    def test_neither_antimeridian_cross(self):
        """
        Test overlaps and non-overlaps between two regions, neither of which cross the antimeridian
        """

        self.assertTrue(FQR([0, 0, 20, 20]).overlaps(FQR([10, 10, 30, 30])), "expected: regions overlap")

        self.assertFalse(FQR([0, 0, 20, 20]).overlaps(FQR([30, 30, 40, 40])), "expected: no overlap - disjoint lat and lon")
        self.assertFalse(FQR([0, 0, 20, 20]).overlaps(FQR([10, 30, 30, 40])), "expected: no overlap - disjoint only lat")
        self.assertFalse(FQR([0, 0, 20, 20]).overlaps(FQR([30, 10, 40, 30])), "expected: no overlap - disjoint only lon")

        self.assertFalse(FQR([0, 0, 20, 20]).overlaps(FQR([20, 0, 40, 20])), "expected: no overlap - borders on lon")
        self.assertFalse(FQR([0, 0, 20, 20]).overlaps(FQR([0, 20, 20, 40])), "expected: no overlap - borders on lat")

    def test_one_antimeridian_cross(self):
        """
        Test overlaps and non-overlaps between two regions, one of which crosses the antimeridian
        """

        self.assertTrue(FQR([160, 0, -160, 20]).overlaps(FQR([-170, 0, -150, 20])), "expected: overlap - east of antimeridian (-170 to -160)")
        self.assertTrue(FQR([160, 0, -160, 20]).overlaps(FQR([150, 0, 170, 20])), "expected: overlap - west of antimeridian (160 to 170)")

        self.assertFalse(FQR([160, 0, -160, 20]).overlaps(FQR([-150, 0, -140, 20])), "expected: no overlap - east of antimeridian")
        self.assertFalse(FQR([160, 0, -160, 20]).overlaps(FQR([140, 0, 150, 20])), "expected: no overlap - west of antimeridian")

    def test_both_antimeridian_cross(self):
        """
        Test overlaps and non-overlaps between two antimeridian-crossing regions
        """

        self.assertTrue(FQR([160, 0, -160, 20]).overlaps(FQR([170, 0, -150, 20])), "expected: overlap - first region starts and ends more east than second region does")
        self.assertTrue(FQR([160, 0, -160, 20]).overlaps(FQR([150, 0, -170, 20])), "expected: overlap - first region starts and ends more west than second region does")
        self.assertTrue(FQR([160, 0, -160, 20]).overlaps(FQR([170, 0, -170, 20])), "expected: overlap - first region fully contains second region")
        self.assertTrue(FQR([170, 0, -170, 20]).overlaps(FQR([160, 0, -160, 20])), "expected: overlap - second region fully contains first region")

    def test_antimeridian_sliver(self):
        """
        Test overlaps and non-overlaps related to the extreme longitudes, self.MIN_ALLOWED_LON and 180
        """

        self.assertFalse(FQR([160, 0, 180, 20]).overlaps(FQR([self.MIN_ALLOWED_LON, 0, -150, 20])),
            f"expected: no overlap - the regions have a gap between 180 and {self.MIN_ALLOWED_LON}")
        self.assertFalse(FQR([160, 0, 180, 20]).overlaps(FQR([180, 0, -150, 20])),
            "expected: no overlap - the regions share a border on 180")
        self.assertFalse(FQR([160, 0, self.MIN_ALLOWED_LON, 20]).overlaps(FQR([self.MIN_ALLOWED_LON, 0, -150, 20])),
            f"expected: no overlap - the regions share a border on {self.MIN_ALLOWED_LON}")

        self.assertTrue(FQR([160, 0, self.MIN_ALLOWED_LON, 20]).overlaps(FQR([180, 0, -150, 20])),
            f"expected: overlap - the regions overlap, barely between 180 and {self.MIN_ALLOWED_LON}")
        self.assertTrue(FQR([180, 0, self.MIN_ALLOWED_LON, 20]).overlaps(FQR([180, 0, -150, 20])),
            f"expected: overlap - the first region is just the sliver between 180 and {self.MIN_ALLOWED_LON}, and is fully contained in the second, which extends to the east")
        self.assertTrue(FQR([180, 0, self.MIN_ALLOWED_LON, 20]).overlaps(FQR([170, 0, self.MIN_ALLOWED_LON, 20])),
            f"expected: overlap - the first region is just the sliver between 180 and {self.MIN_ALLOWED_LON}, and is fully contained in the second, which extends to the west")

if __name__ == "__main__":
    unittest.main()
