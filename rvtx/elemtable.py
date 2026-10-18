"""Global/ElemTable of a family document (2024+: 40-byte rows; header u16 0x0583 + u32 count). Own analysis, verified against Revit-saved rfa."""
import struct

HDR = b'\x83\x05'
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


def build(all_ids, own, owners, family_id, special_neg=()):
    """all_ids: every element id of the document; own: ids that belong to the family itself; owners: {id: 8 owner bytes} from the content doc;
    special_neg: ids of shared rows with owner -1 (KeynoteTable, AssemblyCodeTable)"""
    out = bytearray(HDR + struct.pack('<I', len(all_ids)))
    fam = family_id.to_bytes(8, 'little')
    for i in sorted(all_ids):
        idb = i.to_bytes(8, 'little')
        if i in special_neg: out += idb + b'\0' * 12 + idb + NEG8 + b'\0\0\0\0'
        elif i in own: out += idb + b'\0' * 8 + b'\xff\xff\xff\xff' + idb + owners.get(i, NEG8) + b'\0\0\0\0'
        else: out += idb + b'\0' * 12 + idb + fam + b'\0\0\0\0'
    out += b'\0\0\0\0\xff\xff\xff\xff\x01\x09\0\0' + max(all_ids).to_bytes(8, 'little') + b'\0\0\0\0'
    return bytes(out)
