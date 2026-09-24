"""Apply the same offline board/overlay/hash guards to the repaired candidate."""

from tests import test_z7020_author_loader as baseline


class TestRepairedLoader(baseline.TestAuthorLoader):
    image_filename = baseline.redpitaya.Z20_REPAIRED_BITSTREAM_FILENAME
    image_sha256 = baseline.redpitaya.Z20_REPAIRED_BITSTREAM_SHA256
    lineage = 'common-pid-fixes-e747916'
    repaired = True

    def test_repaired_and_original_images_are_distinct(self):
        self.assertIsNotNone(self.image_sha256)
        self.assertNotEqual(self.image_sha256, baseline.redpitaya.Z20_AUTHOR_BITSTREAM_SHA256)
        self.assertNotEqual(self.image_filename, baseline.redpitaya.Z20_AUTHOR_BITSTREAM_FILENAME)
