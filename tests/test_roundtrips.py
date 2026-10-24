import os
"""Deterministic round trips using only synthetic records and stream bytes."""

import random
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import olefile

from rvtx import cfbw, partition, elemtable


def random_bytes(rng, size):
    return bytes(rng.getrandbits(8) for _ in range(size))


class CfbRoundTripTests(unittest.TestCase):
    def setUp(self):
        rng = random.Random(1701)
        self.paths = [entry[0] for entry in cfbw.RFA_DIR if entry[1] == 2]
        sizes = (0, 1, 63, 64, 4095, 4096, 5000, 100000, 0, 1, 63, 64, 4095)
        self.assertEqual(len(self.paths), len(sizes))
        self.streams = {
            path: random_bytes(rng, size)
            for path, size in zip(self.paths, sizes)
        }

    def test_streams_round_trip(self):
        data = cfbw.write_rfa(self.streams)
        self.assertEqual(data[:8], bytes.fromhex("d0cf11e0a1b11ae1"))
        self.assertEqual(len(data) % 4096, 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.rfa"
            path.write_bytes(data)
            with olefile.OleFileIO(str(path)) as compound:
                paths = compound.listdir(streams=True, storages=False)
                self.assertEqual(
                    {tuple(path) for path in paths},
                    {tuple(path.split("/")) for path in self.paths},
                )
                for name, expected in self.streams.items():
                    with self.subTest(stream=name):
                        with compound.openstream(name.split("/")) as stream:
                            self.assertEqual(stream.read(), expected)

    def test_unexpected_stream_is_rejected(self):
        streams = dict(self.streams, UnexpectedStream=b"")
        with self.assertRaises(AssertionError):
            cfbw.write_rfa(streams)

    def test_output_is_deterministic(self):
        self.assertEqual(
            cfbw.write_rfa(self.streams), cfbw.write_rfa(self.streams)
        )


class PartitionRoundTripTests(unittest.TestCase):
    def make_doc(self, width, seed):
        rng = random.Random(seed)
        neg = (1 << (8 * width)) - 1
        doc = {}
        for region in ("H", "R", "Z"):
            records = []
            # Exercise the high half of 64-bit ids as well as ordinary 32-bit ids.
            identifier = (1 << 40) if width == 8 else 0
            for _ in range(50):
                identifier += rng.randint(1, 100)
                body = random_bytes(rng, rng.randint(2, 300))
                if region == "H":
                    records.append((identifier, body))
                else:
                    # serialize ignores supplied stamps and recomputes them.
                    records.append((identifier, body, 0))
            records.append((neg, b"") if region == "H" else (neg, b"", 1))
            doc[region] = records
        return doc

    def assert_round_trip(self, docs, width):
        joined, items = partition.serialize(docs, width)
        parsed = partition.parse_joined(joined, width)
        self.assertEqual(len(parsed), len(docs))
        self.assertEqual(len(items), sum(len(r) for d in docs for r in d.values()))
        neg = (1 << (8 * width)) - 1
        for index, (original, actual) in enumerate(zip(docs, parsed)):
            with self.subTest(document=index):
                self.assertEqual(actual["H"], original["H"])
                for region in ("R", "Z"):
                    with self.subTest(region=region):
                        expected = [
                            (identifier, body,
                             1 if identifier == neg else partition.adler(body))
                            for identifier, body, _ in original[region]
                        ]
                        self.assertEqual(actual[region], expected)

    def test_one_document_round_trip(self):
        for width in (4, 8):
            with self.subTest(width=width):
                self.assert_round_trip([self.make_doc(width, 2701)], width)

    def test_two_documents_round_trip(self):
        for width in (4, 8):
            with self.subTest(width=width):
                docs = [self.make_doc(width, seed) for seed in (2702, 2703)]
                self.assert_round_trip(docs, width)

    def test_adler_matches_zlib(self):
        # The implementation is zlib.adler32(body) & 0xFFFFFFFF: an unsigned
        # 32-bit checksum, equal to Python 3's already unsigned zlib result.
        for body in (b"", b"abc"):
            with self.subTest(body=body):
                self.assertEqual(partition.adler(body), zlib.adler32(body))


class ElementTableRoundTripTests(unittest.TestCase):
    def test_table_layout_and_own_rows_round_trip(self):
        rng = random.Random(3701)
        all_ids = rng.sample(range(1, 100000), 20)
        own = set(all_ids[:7])
        special_neg = {all_ids[7]}
        owners = {identifier: random_bytes(rng, 8) for identifier in own}
        family_id = 123456789
        table = elemtable.build(all_ids, own, owners, family_id, special_neg)

        self.assertTrue(table.startswith(elemtable.HDR))
        count_offset = len(elemtable.HDR)
        self.assertEqual(struct.unpack_from("<I", table, count_offset)[0], 20)
        row_start = count_offset + 4
        row_end = row_start + 40 * len(all_ids)
        self.assertEqual(len(table), row_end + 24)
        rows = [table[offset:offset + 40]
                for offset in range(row_start, row_end, 40)]
        self.assertEqual(
            [int.from_bytes(row[:8], "little") for row in rows],
            sorted(all_ids),
        )
        own_rows = []
        for identifier, row in zip(sorted(all_ids), rows):
            with self.subTest(identifier=identifier):
                self.assertEqual(len(row), 40)
                self.assertEqual(row[20:28], row[:8])
                self.assertEqual(row[36:40], b"\0" * 4)
                if identifier in own:
                    self.assertEqual(row[8:20], b"\0" * 8 + b"\xff" * 4)
                    self.assertEqual(row[28:36], owners[identifier])
                    own_rows.append(row)
                else:
                    self.assertEqual(row[8:20], b"\0" * 12)
                    expected_owner = (
                        b"\xff" * 8 if identifier in special_neg
                        else family_id.to_bytes(8, "little")
                    )
                    self.assertEqual(row[28:36], expected_owner)

        # Trailer: zero u32, -1 u32, year-specific u16, zero u16,
        # maximum id u64, then zero u32.
        trailer = table[row_end:]
        self.assertEqual(
            trailer,
            b"\0" * 4 + b"\xff" * 4 + elemtable.TRAILER_CONST
            + b"\0" * 2 + max(all_ids).to_bytes(8, "little") + b"\0" * 4,
        )
        self.assertEqual(int.from_bytes(trailer[12:20], "little"), max(all_ids))
        self.assertEqual(elemtable.cd_rows(b"".join(own_rows), W=8), owners)


if __name__ == "__main__":
    unittest.main()


class ElementTable4Tests(unittest.TestCase):
    def test_four_byte_rows_are_28_bytes_and_keep_cd_words(self):
        ids = [5, 9, 12, 20]
        owners = {9: b"\x01\x02\x03\x04" + b"\xcf\x03\x00\x00" + b"\xef\x03\x00\x00"}
        os.environ['RVTX_ETDATES'] = 'old'      # the test pins the project-dates mode
        try: table = elemtable.build4(ids, {9}, owners, 77, special_neg={20})
        finally: os.environ.pop('RVTX_ETDATES', None)
        rows = [table[6 + 28 * k:6 + 28 * (k + 1)] for k in range(4)]
        self.assertEqual(len(table), 6 + 28 * 4 + 12 + len(elemtable.TRAILER_TABLE4))
        self.assertEqual(rows[1], struct.pack("<II", 9, 9) + b"\xcf\x03\x00\x00\xef\x03\x00\x00" + b"\xef\x03\x00\x00" + b"\0" * 4 + b"\x01\x02\x03\x04")
        self.assertEqual(rows[0][-4:], struct.pack("<I", 77))
        self.assertEqual(rows[3][-4:], b"\xff" * 4)


class NullExprTests(unittest.TestCase):
    def test_absent_expression_uses_pointer_form(self):
        from rvtx import rfa
        t = {'obj': {'m_pairs': [{'name': 'a', 'params': {'m_params': [{'m_oExpression': None, 'm_value': 1.0}, {'m_oExpression': {'obj': 1}}]}}]}}
        rfa._null_exprs(t)
        ps = t['obj']['m_pairs'][0]['params']['m_params']
        self.assertEqual(ps[0]['m_oExpression'], {'null': 0})
        self.assertEqual(ps[1]['m_oExpression'], {'obj': 1})
