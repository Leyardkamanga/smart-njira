import pytest
from app import parse_location, get_directions

def test_parse_coordinates():
    assert parse_location("-14.0, 33.8") == (33.8, -14.0)

def test_parse_place_name():
    result = parse_location("Lilongwe")
    assert isinstance(result, tuple) and len(result) == 2

def test_invalid_input():
    result = parse_location("definitelynonexistent123456")
    assert isinstance(result, tuple) or result is None


def test_routing():
    origin = (-14.0, 33.8)
    dest = (-15.8, 35.0)
    route_xy, tooltip, dist, dur, geojson = get_directions(origin, dest, "Car")
    assert isinstance(route_xy, list) and len(route_xy) > 0
    assert dist > 0 and dur > 0
