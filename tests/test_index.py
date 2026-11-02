import tempfile
import unittest
from pathlib import Path
from similarity_gallery.index import discover_images

class IndexTests(unittest.TestCase):
    def test_finds_images_without_using_filename_or_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "pic one.JPG").write_bytes(b"stub")
            (folder / "friend_sent.heic").write_bytes(b"stub")
            (folder / "notes.txt").write_text("not a photo")
            nested = folder / "nested"
            nested.mkdir()
            (nested / "screenshot.png").write_bytes(b"stub")
            found = discover_images(folder)
            self.assertEqual({p.name for p in found},
                             {"pic one.JPG", "friend_sent.heic", "screenshot.png"})

    def test_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for i in range(10):
                (folder / f"{i}.jpg").write_bytes(b"")
            self.assertEqual(len(discover_images(folder, 3)), 3)

if __name__ == "__main__":
    unittest.main()
