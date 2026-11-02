import unittest
import numpy as np
from similarity_gallery.similarity import normalize, similarity_groups, continuous_order, find_similar

class SimilarityTests(unittest.TestCase):
    def setUp(self):
        self.vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.99, 0.01, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)

    def test_normalize(self):
        vectors = normalize(self.vectors)
        np.testing.assert_allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)

    def test_find_similar(self):
        self.assertEqual(find_similar(self.vectors, 0, 1)[0][0], 1)

    def test_groups_include_all_photos(self):
        groups = similarity_groups(self.vectors, 0.9)
        self.assertEqual(sorted(i for group in groups for i in group), [0, 1, 2, 3])
        self.assertTrue(any(set(group) == {0, 1} for group in groups))

    def test_continuous_roll_includes_every_photo(self):
        indices = continuous_order(self.vectors)
        self.assertEqual(indices[:2], [0, 1])
        self.assertEqual(sorted(indices), [0, 1, 2, 3])

    def test_empty_roll(self):
        self.assertEqual(continuous_order(np.empty((0, 3))), [])

if __name__ == "__main__":
    unittest.main()
