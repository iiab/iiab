class FQR:
    """
    A valid FQR that should be ready to save to meta.json or pass to the
    pmtiles tool.
    """

    # Convert from

    def __init__(self, bbox):
        self._init_from_bbox(bbox)

    def _init_from_bbox(self, bbox):
        """
        Initialize values from `bbox` (i.e, a list of 4 numbers). Check if `bbox`
        meets our standard format, including the basic structure.
        """

        if not isinstance(bbox, list):
            raise TypeError("bbox is not an array")
        if len(bbox) != 4:
            raise ValueError("bbox has unexpected length")
        for coord in bbox:
            if not isinstance(coord, (int, float)):
                raise TypeError("coordinate is not a number")

        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bbox

        if self.min_lon == self.max_lon:
            raise ValueError("longitudes are equal")
        for lon in [self.min_lon, self.max_lon]:
            if lon > 180:
                raise ValueError("longitude > 180")
            if lon <= -180:
                raise ValueError(f"longitude <= -180")

        if self.min_lat >= self.max_lat:
            raise ValueError("latitudes are equal or out of order")
        for lat in [self.min_lat, self.max_lat]:
            if lat > 90:
                raise ValueError("latitude > 90")
            if lat < -90:
                raise ValueError("latitude < -90")

    @classmethod
    def from_bbox_str(cls, bbox_str):
        """
        This function parses and validates the bbox string that comes from the
        UI tool (the same format that gets passed into pmtiles), and
        initializes an FQR from it.

        An example string in this format is `"0,10,50.5,60.5"`
        """
        try:
            bbox = [float(n) for n in bbox_str.split(",")]
        except Exception as e:
            raise ValueError(f"bbox ({bbox_str}) is malformed: {e}")

        try:
            return cls(bbox)
        except Exception as e:
            raise ValueError(f"bbox ({bbox}) is invalid: {e}")


    # Convert to

    def to_bbox(self):
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    def to_bbox_str(self):
        return ",".join(map(repr, self.to_bbox()))


    # Check for overlaps

    def crosses_antimeridian(self):
        return self.min_lon > self.max_lon

    def overlaps(self, other):
        # We can rule out latitude non-overlap right away so we don't have
        # to check it again while dealing with the complicated longitude logic:
        if self.min_lat >= other.max_lat or other.min_lat >= self.max_lat:
            return False

        # If both regions cross the antimeridian, it's guaranteed that there's
        # some overlap:
        if self.crosses_antimeridian() and other.crosses_antimeridian():
            return True

        # If neither region crosses the antimeridian, our overlap logic is pretty simple. The regions
        #   do not overlap IFF `self` is fully east or fully west of the other (sharing a border does
        #   not count as not overlapping). In other words:
        #
        # self.min_lon >= other.max_lon
        # self:                [      ]
        # other:     [      ]
        #
        # other.min_lon >= self.max_lon
        # self:      [      ]
        # other:               [      ]
        #
        # So our condition is:
        #
        # not ((self.min_lon >= other.max_lon) or (other.min_lon >= self.max_lon))
        #
        # Which simplifies to:
        #
        # (self.min_lon < other.max_lon) and (other.min_lon < self.max_lon)
        if not self.crosses_antimeridian() and not other.crosses_antimeridian():
            return (
                self.min_lon < other.max_lon and
                other.min_lon < self.max_lon
            )

        # At this point we know that exactly one of `self` or `other` crosses the antimeridian.
        #
        # If `self` crosses the antimeridian and `other` does not, it means that:
        # * `self` exists in two parts:
        #   * between `self.min_lon` and 180
        #   * between -180 and `self.max_lon`
        # * `other` exists in one part:
        #   * between `other.min_lon` and `other.max_lon`
        #
        # The first type of overlap is if the eastern end of
        #   `other` (i.e. `other.max_lon`) is east of `self.min_lon`:
        #
        # self:             [     |    ]
        # other:     [        ]   |
        #
        # The second type of overlap is if the western end of
        #    `other` (i.e. `other.min_lon`) is west of `self.max_lon`:
        #
        # self:             [     |    ]
        # other:                  | [        ]
        #
        # So we end up with this condition:
        #
        # (self.min_lon < other.max_lon) or (other.min_lon < self.max_lon)
        #
        # Okay. So what if `other` crosses the antimeridian and `self` does not?
        #   Just swap the fqrs:
        #
        # (other.min_lon < self.max_lon) or (self.min_lon < other.max_lon)
        #
        # What if we change the order of the two parts of the `or`?
        #
        # (self.min_lon < other.max_lon) or (other.min_lon < self.max_lon)
        #
        # Either by coincidence, or perhaps some basic principle of modular arithmetic,
        # this ends up being the same test! So this is the only test we need here.
        return (
            self.min_lon < other.max_lon or
            other.min_lon < self.max_lon
        )
