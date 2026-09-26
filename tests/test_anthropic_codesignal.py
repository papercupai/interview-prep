"""Regression tests and learner checks for the original ICA prep exercises.

Reference: python3 -m unittest discover -s tests -p 'test_anthropic_codesignal.py' -v
Your work: python3 tests/test_anthropic_codesignal.py --practice [-k Level1]
"""
import importlib.util
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRACTICE = '--practice' in sys.argv
if PRACTICE:
    sys.argv.remove('--practice')
target = ROOT / ('anthropic-codesignal-practice.py' if PRACTICE else 'anthropic-codesignal-solutions.py')
spec = importlib.util.spec_from_file_location('exercise', target)
exercise = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exercise)
ReviewQueue = exercise.ReviewQueue


class Drills(unittest.TestCase):
    def test_ranking_ties_and_limits(self):
        events = ['b', 'a', 'b', 'a', 'c']
        self.assertEqual(exercise.ranked_counts(events, 2), ['a', 'b'])
        self.assertEqual(exercise.ranked_counts(events, 8), ['a', 'b', 'c'])
        self.assertEqual(exercise.ranked_counts(events, 0), [])
        self.assertEqual(exercise.ranked_counts(events, -1), [])
        self.assertEqual(exercise.ranked_counts([], 3), [])
        self.assertEqual(events, ['b', 'a', 'b', 'a', 'c'])

    def test_merge_overlap_nesting_duplicates_and_touching(self):
        windows = [(5, 8), (1, 4), (3, 6), (8, 9), (1, 4), (2, 3)]
        self.assertEqual(exercise.merge_windows(windows), [(1, 8), (8, 9)])
        self.assertEqual(windows, [(5, 8), (1, 4), (3, 6), (8, 9), (1, 4), (2, 3)])
        self.assertEqual(exercise.merge_windows([]), [])
        self.assertEqual(exercise.merge_windows([(-3, -1), (-1, 2)]), [(-3, -1), (-1, 2)])

    def test_merge_against_overlap_components(self):
        rng = random.Random(42)
        for _ in range(100):
            windows = [(a, a + rng.randint(1, 5)) for a in rng.choices(range(-5, 6), k=10)]
            components = []
            remaining = set(range(len(windows)))
            while remaining:
                group = {remaining.pop()}
                while True:
                    neighbors = {i for i in remaining if any(
                        max(windows[i][0], windows[j][0]) < min(windows[i][1], windows[j][1])
                        for j in group)}
                    if not neighbors:
                        break
                    group.update(neighbors)
                    remaining.difference_update(neighbors)
                components.append((min(windows[i][0] for i in group), max(windows[i][1] for i in group)))
            self.assertEqual(exercise.merge_windows(windows), sorted(components))

    def test_requests_boundary_and_rejection_does_not_extend_window(self):
        events = [('a', 0), ('a', 2), ('b', 3), ('a', 5), ('b', 7), ('b', 8)]
        self.assertEqual(exercise.accepted_requests(events, 5), [('a', 0), ('b', 3), ('a', 5), ('b', 8)])
        self.assertEqual(exercise.accepted_requests([('a', 0), ('a', 0)], 0), [('a', 0), ('a', 0)])
        self.assertEqual(exercise.accepted_requests([], 5), [])


class Level1(unittest.TestCase):
    def test_crud_and_zero(self):
        q = ReviewQueue()
        self.assertIsNone(q.get('a'))
        self.assertIs(q.add('a', 0), True)
        self.assertEqual(q.get('a'), 0)
        self.assertIs(q.add('a', 100), False)
        self.assertEqual(q.get('a'), 0)
        self.assertIs(q.set_priority('missing', 2), False)
        self.assertIs(q.set_priority('a', 3), True)
        self.assertEqual(q.get('a'), 3)
        self.assertIs(q.delete('a'), True)
        self.assertIsNone(q.get('a'))
        self.assertIs(q.delete('a'), False)

    def test_instances_are_independent(self):
        a, b = ReviewQueue(), ReviewQueue()
        a.add('x', 7)
        self.assertIsNone(b.get('x'))


class Level2(unittest.TestCase):
    def test_ordering_update_delete_and_limits(self):
        q = ReviewQueue()
        for key, value in [('b', 3), ('a', 3), ('z', 0)]:
            q.add(key, value)
        self.assertEqual(q.top(9), ['a', 'b', 'z'])
        self.assertEqual(q.top(1), ['a'])
        self.assertEqual(q.top(0), [])
        self.assertEqual(q.top(-1), [])
        q.set_priority('z', 4)
        self.assertEqual(q.top(9), ['z', 'a', 'b'])
        q.delete('a')
        self.assertEqual(q.top(9), ['z', 'b'])

    def test_results_do_not_expose_internal_state(self):
        q = ReviewQueue()
        q.add('a', 1)
        q.top(3).clear()
        self.assertEqual(q.top(3), ['a'])
        self.assertEqual(ReviewQueue().top(1), [])


class Level3(unittest.TestCase):
    def setUp(self):
        self.q = ReviewQueue()
        self.q.add('a', 2)
        self.q.add('b', 1)

    def test_exact_expiry_boundary(self):
        self.assertIs(self.q.claim('a', 'w1', 10, 5), True)
        self.assertEqual(self.q.ready(14, 10), ['b'])
        self.assertIs(self.q.complete('a', 'w1', 15), False)
        self.assertEqual(self.q.ready(15, 10), ['a', 'b'])
        self.assertIs(self.q.claim('a', 'w2', 15, 2), True)
        self.assertIs(self.q.complete('a', 'w1', 16), False)
        self.assertIs(self.q.complete('a', 'w2', 16), True)
        self.assertIsNone(self.q.get('a'))

    def test_validation_ownership_and_top_backwards_compatibility(self):
        self.assertIs(self.q.claim('missing', 'w', 0, 4), False)
        self.assertIs(self.q.claim('a', 'w', 0, 0), False)
        self.assertIs(self.q.claim('a', 'w', 0, -1), False)
        self.assertIs(self.q.claim('a', 'w', 0, 4), True)
        self.assertIs(self.q.claim('a', 'w', 1, 8), False)
        self.assertIs(self.q.complete('a', 'other', 1), False)
        self.q.set_priority('a', 9)
        self.assertEqual(self.q.top(9), ['a', 'b'])
        self.assertEqual(self.q.ready(1, 9), ['b'])
        self.assertIs(self.q.complete('b', 'w', 1), False)

    def test_delete_readd_clears_lease(self):
        self.q.claim('a', 'w', 0, 10)
        self.q.delete('a')
        self.q.add('a', 0)
        self.assertIs(self.q.complete('a', 'w', 1), False)
        self.assertEqual(self.q.ready(1, 9), ['b', 'a'])

    def test_multiple_simultaneous_expirations(self):
        self.q.claim('a', 'w', 0, 2)
        self.q.claim('b', 'w', 0, 2)
        self.assertEqual(self.q.ready(2, 9), ['a', 'b'])


class Level4(unittest.TestCase):
    def setUp(self):
        self.q = ReviewQueue()
        for key, value in [('a', 3), ('b', 2), ('c', 1)]:
            self.q.add(key, value)

    def test_success_and_prior_contracts(self):
        self.assertIs(self.q.bulk_claim(['a', 'b'], 'w', 0, 5), True)
        self.assertEqual(self.q.ready(0, 9), ['c'])
        self.assertEqual(self.q.top(9), ['a', 'b', 'c'])
        self.assertIs(self.q.complete('a', 'other', 1), False)
        self.assertIs(self.q.complete('a', 'w', 1), True)
        self.assertEqual(self.q.ready(5, 9), ['b', 'c'])

    def test_failure_is_atomic_for_missing_and_busy_ids(self):
        self.assertIs(self.q.bulk_claim(['a', 'missing'], 'w', 0, 5), False)
        self.assertEqual(self.q.ready(0, 9), ['a', 'b', 'c'])
        self.q.claim('b', 'other', 0, 5)
        self.assertIs(self.q.bulk_claim(['a', 'b'], 'w', 1, 5), False)
        self.assertEqual(self.q.ready(1, 9), ['a', 'c'])
        self.assertIs(self.q.complete('b', 'other', 1), True)

    def test_reject_duplicate_empty_and_nonpositive_ttl(self):
        for ids, ttl in [(['a', 'a'], 5), ([], 5), (['a'], 0), (['a'], -1)]:
            self.assertIs(self.q.bulk_claim(ids, 'w', 0, ttl), False)
            self.assertEqual(self.q.ready(0, 9), ['a', 'b', 'c'])

    def test_expiry_runs_before_batch_validation(self):
        self.q.claim('a', 'old', 0, 5)
        self.assertIs(self.q.bulk_claim(['a', 'missing'], 'new', 5, 5), False)
        self.assertEqual(self.q.ready(5, 9), ['a', 'b', 'c'])
        self.assertIs(self.q.bulk_claim(['a', 'b'], 'new', 5, 5), True)
        self.assertIs(self.q.complete('a', 'old', 5), False)
        self.assertIs(self.q.complete('a', 'new', 5), True)


if __name__ == '__main__':
    unittest.main()
