# -*- coding: utf-8 -*-
"""Testy co_nowego.py (bez okien): python2.7 -m unittest test_co_nowego
(dziala tez w Pythonie 3)."""

import os, io, json, shutil, tempfile, datetime, unittest

import co_nowego

TODAY = datetime.date(2026, 11, 23)


def entry(n, data='2026-11-23', **extra):
    item = {'id': 'e%d' % n, 'data': data, 'tekst': u'Nowość %d.' % n}
    item.update(extra)
    return item


class SelectTest(unittest.TestCase):

    def test_waiting_after_a_break(self):
        # Po dlugiej przerwie - wszystkie zalegle, nie tylko ostatnia
        entries = [entry(3), entry(2, '2026-11-01'), entry(1, '2026-10-01')]
        waiting, save = co_nowego.select(entries, set(['e1']), {}, TODAY)
        self.assertEqual([e['id'] for e in waiting], ['e3', 'e2'])
        self.assertIsNone(save)

    def test_first_run_skips_old(self):
        entries = [entry(3), entry(2, '2026-11-17'), entry(1, '2026-11-15')]
        waiting, save = co_nowego.select(entries, None, {}, TODAY)
        self.assertEqual([e['id'] for e in waiting], ['e3', 'e2'])
        self.assertEqual(save, set(['e1']))

    def test_first_run_nothing_old(self):
        waiting, save = co_nowego.select([entry(1)], None, {}, TODAY)
        self.assertEqual(len(waiting), 1)
        self.assertEqual(save, set())  # plik powstaje - nastepny start to nie pierwszy

    def test_all_heard(self):
        waiting, save = co_nowego.select([entry(1)], set(['e1']), {}, TODAY)
        self.assertEqual(waiting, [])

    def test_needs(self):
        entries = [entry(1, wymaga='wicero'), entry(2, wymaga='kompan'), entry(3)]
        waiting, _ = co_nowego.select(entries, set(), {'wicero': False}, TODAY)
        # kompan - nieznany w features: pokazujemy
        self.assertEqual([e['id'] for e in waiting], ['e2', 'e3'])

    def test_24_all_shown(self):
        entries = [entry(n) for n in range(24)]
        waiting, save = co_nowego.select(entries, set(), {}, TODAY)
        self.assertEqual(len(waiting), 24)
        self.assertIsNone(save)

    def test_25_newest_10_and_all_heard(self):
        entries = [entry(n) for n in range(30)]
        heard = set(['e0', 'e1', 'e2', 'e3', 'e4'])
        waiting, save = co_nowego.select(entries, heard, {}, TODAY)
        self.assertEqual([e['id'] for e in waiting], ['e%d' % n for n in range(5, 15)])
        self.assertEqual(save, set(e['id'] for e in entries))


class FilesTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.entries = os.path.join(self.dir, 'co_nowego.json')
        self.heard = os.path.join(self.dir, 'ap', 'uslyszane.json')

    def tearDown(self):
        shutil.rmtree(self.dir)

    def write(self, entries):
        text = json.dumps(entries, ensure_ascii=False)
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        with io.open(self.entries, 'w', encoding='utf-8') as f:
            f.write(text)

    def pending(self):
        return co_nowego.pending({}, TODAY, self.entries, self.heard)

    def test_order_newest_first(self):
        self.write([entry(1, '2026-11-20'), entry(2), entry(3), entry(4, '2026-11-21')])
        self.assertEqual([e['id'] for e in self.pending()], ['e3', 'e2', 'e4', 'e1'])

    def test_interrupted_reading(self):
        # Przeczytane do konca tylko e2 - AP wylaczone; przy nastepnym starcie e1
        self.write([entry(1), entry(2)])
        self.assertEqual(len(self.pending()), 2)
        co_nowego.mark_heard('e2', self.heard)
        self.assertEqual([e['id'] for e in self.pending()], ['e1'])
        co_nowego.mark_heard('e1', self.heard)
        self.assertEqual(self.pending(), [])

    def test_new_entry_after_update(self):
        self.write([entry(1)])
        co_nowego.mark_heard('e1', self.heard)
        self.write([entry(1), entry(2, '2026-12-01')])
        self.assertEqual([e['id'] for e in self.pending()], ['e2'])

    def test_broken_file_starts_ap(self):
        with io.open(self.entries, 'w', encoding='utf-8') as f:
            f.write(u'{zepsuty')
        self.assertEqual(self.pending(), [])

    def test_repo_file_is_valid(self):
        entries = co_nowego.load_entries()
        ids = [e['id'] for e in entries]
        self.assertEqual(len(ids), len(set(ids)))
        for e in entries:
            co_nowego._date(e['data'])
            self.assertTrue(e['tekst'].strip())


class HeadingTest(unittest.TestCase):

    def test_headings(self):
        self.assertEqual(co_nowego.heading(0, 1), u'Cześć! Jest nowość w AP.')
        self.assertEqual(co_nowego.heading(0, 3), u'Cześć! Są nowości w AP. Pierwsza z trzech:')
        self.assertEqual(co_nowego.heading(1, 3), u'Druga z trzech:')
        self.assertEqual(co_nowego.heading(4, 5), u'Piąta z pięciu:')
        self.assertEqual(co_nowego.heading(20, 22), u'Dwudziesta pierwsza z dwudziestu dwóch:')
        self.assertEqual(co_nowego.heading(23, 24), u'Dwudziesta czwarta z dwudziestu czterech:')


if __name__ == '__main__':
    unittest.main()
