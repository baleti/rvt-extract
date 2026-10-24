"""Global/ElemTable of a family document (2024+: 40-byte rows; header u16 0x0583 + u32 count). Own analysis, verified against Revit-saved rfa."""
import struct, os

HDR = b'\x83\x05'
TRAILER_CONST = b'\x01\x09'       # u16 at trailer+8, from the project's ElemTable (year specific)
TAG = None
NEG8 = b'\xff' * 8


def cd_rows(seg, W=8):
    """rows [id][a][b][ffffffff][id][owner][0] of a content-document segment: {id: owner bytes}"""
    rows = {}
    n = len(seg) - 40
    k = 0
    while k <= n:
        if seg[k + 16:k + 20] == b'\xff\xff\xff\xff' and seg[k + 20:k + 28] == seg[k:k + 8] and seg[k + 36:k + 40] == b'\0\0\0\0':
            i = int.from_bytes(seg[k:k + 8], 'little')
            if 0 < i < 1 << 40 and i not in rows: rows[i] = seg[k + 28:k + 36]
            k += 40
        else: k += 1
    return rows


def build(all_ids, own, owners, family_id, special_neg=(), shared_owner=None):
    """all_ids: every element id of the document; own: ids that belong to the family itself; owners: {id: 8 owner bytes} from the content doc;
    special_neg: ids of shared rows with owner -1 (KeynoteTable, AssemblyCodeTable)"""
    out = bytearray((TAG or HDR) + struct.pack('<I', len(all_ids)))
    fam = family_id.to_bytes(8, 'little')
    for i in sorted(all_ids):
        idb = i.to_bytes(8, 'little')
        if i in special_neg: out += idb + b'\0' * 12 + idb + NEG8 + b'\0\0\0\0'
        elif i in own: out += idb + b'\0' * 8 + b'\xff\xff\xff\xff' + idb + owners.get(i, NEG8) + b'\0\0\0\0'
        else: out += idb + b'\0' * 12 + idb + (shared_owner[i].to_bytes(8, 'little') if shared_owner and i in shared_owner else fam) + b'\0\0\0\0'
    out += b'\0\0\0\0\xff\xff\xff\xff' + TRAILER_CONST + b'\0\0' + max(all_ids).to_bytes(8, 'little') + b'\0\0\0\0'
    return bytes(out)


# ---- 4-byte element ids (Revit <= 2023): 28-byte rows [id][id][a][b][c][x][owner]; layout from the Revit-written sample families; own/shared variants are inferred (a,b,c zero; own c = ffffffff)
TRAILER_TABLE4 = bytes.fromhex('120000001f140000000000001f1400003f0000005e0000005e000000a814000000000000a81400002e0000006500000065000000b714000000000000b71400002e0000006500000065000000c914000000000000c91400002e0000006500000065000000de14000000000000de1400002e0000006500000065000000f614000000000000f61400002e00000065000000650000000715000000000000071500002e00000065000000650000001715000000000000171500002e00000065000000650000002615000000000000261500002e00000065000000650000002715000000000000271500002e00000065000000470000002815000000000000281500002e00000065000000470000002915000000000000291500002e00000065000000470000002a150000000000002a1500002e00000065000000470000002b150000000000002b1500002e00000065000000470000002c150000000000002c1500002e00000065000000470000002d150000000000002d1500002e00000065000000470000002e150000000000002e1500002e0000006500000047000000941900000000000094190000640000006600000066000000ffffff')     # constant table of built-in element ids Revit writes before the final 12 bytes (identical in the Revit 2019, 2020, 2022 and 2023 sample families)
TRAILER4 = b'\xff\x10\x08\x00'     # u32 before the max id in the trailer, from the project's ElemTable


def cd_rows4(seg):
    rows = {}
    n = len(seg) - 28
    k = 0
    while k <= n:
        if seg[k + 4:k + 8] == seg[k + 8:k + 12] and seg[k + 24:k + 28] == b'\0\0\0\0' and seg[k + 20:k + 24] == b'\xff\xff\xff\xff':
            i = int.from_bytes(seg[k + 4:k + 8], 'little')
            if 0 < i < 1 << 31 and i not in rows: rows[i] = seg[k:k + 4] + seg[k + 12:k + 20]     # owner + the two words a, b (not zero in 4-byte projects)
            k += 28
        else: k += 1
    return rows


def build4(all_ids, own, owners, family_id, special_neg=()):
    out = bytearray((TAG or HDR) + struct.pack('<I', len(all_ids)))
    fam = family_id.to_bytes(4, 'little'); NEG4 = b'\xff\xff\xff\xff'
    for i in sorted(all_ids):
        idb = (i & 0xFFFFFFFF).to_bytes(4, 'little')      # negative / 64-bit sentinel ids wrap to 32 bit
        if i in special_neg: out += idb + idb + b'\0' * 16 + NEG4
        elif i in own:
            ow = owners.get(i, NEG4 + b'\0' * 8)
            c = ow[8:12] if os.environ.get('RVTX_ETC', 'b') == 'b' and ow[8:12] != NEG4 else NEG4     # Revit's own rows: c equals b in 1554 of 1713 rows of the 2019 sample (the project's content row has ffffffff there)
            out += idb + idb + ow[4:12] + c + b'\0\0\0\0' + ow[:4]
        else: out += idb + idb + b'\0' * 16 + fam
    out += (b'' if os.environ.get('RVTX_TRAILER4', '1') == '0' else TRAILER_TABLE4) + TRAILER4 + max([i for i in all_ids if 0 <= i < (1 << 31)] or [0]).to_bytes(4, 'little') + b'\0\0\0\0'
    return bytes(out)
