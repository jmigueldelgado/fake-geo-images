from Fakegeoimages.fakegeoimages import FakeGeoImage


def test_standard_image_4bands():
    test_img = FakeGeoImage(6, 4, 4, "uint16").create()
