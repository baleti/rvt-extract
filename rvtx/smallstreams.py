"""Small rfa streams generated from layout facts (own analysis of Revit 2024 family files); GUIDs are fresh unless given."""
import struct, zlib, uuid, time

BUILD = '20231029_1515(x64)'
FORMAT = '2024'
PREFIX = {'Global/History': 1, 'Global/DocumentIncrementTable': 1, 'Global/PartitionTable': 0, 'Global/ContentDocuments': 1, 'Global/ElemTable': 0, 'Global/Latest': 5}


def g2b(g):
    return uuid.UUID(g).bytes_le if isinstance(g, str) else g


def history(doc_guid, save_guid):
    d, s = g2b(doc_guid), g2b(save_guid)
    return (bytes.fromhex('ff040100000000000000000000000100000000000000') + d + d + d + b'\0' * 16 + d + b'\0\0\0\0' + b'\x01\0\0\0' + s + b'\x28\0\0\0\0')


_DIT = bytes.fromhex('03050100000001000000ffffffffa906000004000000550073006500720000000000000000000100000000000000e24ad46a01000000a90600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff010100000001000000ffffffffa906000004000000550073006500720000000000000000000100000000000000e24ad46a01000000a90600000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff010000000000000000')


def document_increment_table(n_elements, when=None):
    """layout: the element count (u32) appears 4 times and the save time (unix seconds) twice; sample values 1705 / 0x6ad44ae2 are replaced"""
    t = struct.pack('<I', int(when or time.time()))
    return _DIT.replace(struct.pack('<I', 1705), struct.pack('<I', n_elements)).replace(bytes.fromhex('e24ad46a'), t)


def partition_table(part_guid):
    return bytes.fromhex('ec0b0100000001000000') + g2b(part_guid) + bytes.fromhex('00000000ffffffffffffffffffffffff01000000000800000057006f0072006b0073006500740031000100000001000000000000000100000000000000')


def content_documents_empty():
    return bytes.fromhex('7b0300000000ffffffff00000000')


_CONTENTS_HEAD = bytes.fromhex('621922051b000000010000000100000043020000000800000001000100010001000200020004000400040004000400040008000800080008000a00000000000000020000000900d82100000010000000000000') + bytes.fromhex('6219220500000000')


_CONTENTS_RAW = bytes.fromhex('05050000000000000000000000000600000047004c004f00420041004c00000000000000000000000000000000000000000000000000000000000000000000000000010000005269547e9a3e2c4fb39bbca768a3e094feff000000000012000000320030003200330031003000320039005f00310035003100350028007800360034002900070000000000000003000000ffffffff0300000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff5305ffffffff590500000000000000000000000000000000000000000000000000000000')


def contents(part_guid, build=BUILD):
    return _CONTENTS_RAW.replace(g2b('7e546952-3e9a-4f2c-b39b-bca768a3e094'), g2b(part_guid))


def contents_stream(part_guid, template_raw, template_tail):
    raw = template_raw
    raw = raw.replace(g2b('7e546952-3e9a-4f2c-b39b-bca768a3e094'), g2b(part_guid))
    co = zlib.compressobj(6, zlib.DEFLATED, -15); z = co.compress(raw) + co.flush()
    gzh = bytes.fromhex('1f8b080000000000000b')
    return _CONTENTS_HEAD + gzh + z + struct.pack('<II', zlib.crc32(raw) & 0xFFFFFFFF, len(raw)) + template_tail


def transmission_data(kn, ac):
    ref = lambda i, t: ('<ExternalFileReference><ElementId>%d</ElementId><ExternalFileReferenceType>%s</ExternalFileReferenceType><LastSavedPath></LastSavedPath><LastSavedAbsolutePath></LastSavedAbsolutePath>'
                        '<LastSavedPathType>Absolute</LastSavedPathType><LastSavedLoadState>Not Found</LastSavedLoadState><DesiredPath></DesiredPath><DesiredPathType>Absolute</DesiredPathType>'
                        '<DesiredLoadState>Loaded</DesiredLoadState></ExternalFileReference>') % (i, t)
    xml = '<?xml version="1.0"?>\r\n<TransmissionData isTransmitted="false" userData="" version="5">' + ref(kn, 'Keynote Table') + ref(ac, 'Assembly Code Table') + '</TransmissionData>\r\n'
    return struct.pack('<I', len(xml)) + xml.encode('utf-16le')


def part_atom(title, category, filename, when=None):
    w = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(when or time.time()))
    return ('<?xml version="1.0" encoding="UTF-8"?>\r\n<entry xmlns="http://www.w3.org/2005/Atom" xmlns:A="urn:schemas-autodesk-com:partatom"><title>%s</title><id></id><updated>%s</updated>'
            '<A:taxonomy><term>adsk:revit</term><label>Autodesk Revit</label></A:taxonomy><A:taxonomy><term>adsk:revit:grouping</term><label>Autodesk Revit Grouping</label></A:taxonomy>'
            '<category><term>%s</term><scheme>adsk:revit:grouping</scheme></category><link rel="design-2d" type="application/rfa" href="."><A:design-file><A:title>%s</A:title><A:product>Revit</A:product>'
            '<A:product-version>2024</A:product-version><A:updated>%s</A:updated></A:design-file></link><A:family type="user"><A:variationCount>1</A:variationCount><A:part type="user"><title>%s</title></A:part></A:family></entry>'
            % (title, w, category, filename, w, title)).encode('utf-8')


def png_blank(w=128, h=128, rgb=(236, 236, 236)):
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b''.join(b'\0' + bytes(rgb) * w for _ in range(h))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')


_PREVIEW_HEAD = bytes.fromhex('621922051b000000010000000100000043020000000800000001000100010001000200020004000400040004000400040008000800080008000a00000000000000020000000900d82100000010000000000000621922050c8000000b0046696c655072657669657700000700000001000000090000006d5f7041496d6167650e01000000000000ffffffff0d8000000c0041526173746572496d61676500000300000007000000110000006d5f636f6d70726573736564496d61676502500000060000006d5f6470695807000000060000006d5f64706959070000000d0000006d5f7769647468496e46656574070000000e0000006d5f686569676874496e4665657407000000070000006d5f776964746804000000080000006d5f6865696768740400000000000000')


def preview(png=None):
    png = png or png_blank()
    return _PREVIEW_HEAD + struct.pack('<I', len(png) - 40) + png


def basic_file_info(path, save_guid, build=BUILD, fmt=FORMAT):
    P = lambda s: struct.pack('<I', len(s)) + s.encode('utf-16le')
    nul = '00000000-0000-0000-0000-000000000000'
    head = (bytes.fromhex('0e000000') + b'\0' * 10 + P(fmt) + P(build) + P(path) + bytes.fromhex('0300000000') + P(nul) + P('ENU') + bytes.fromhex('0001000000') + P(save_guid) + P(save_guid)
            + bytes.fromhex('010000003100') + P(nul) + b'\0' + P('Autodesk Revit') + P('RevitApplication'))
    text = ('Worksharing: Not enabled\r\nUsername: \r\nCentral Model Path: \r\nFormat: %s\r\nBuild: %s\r\nLast Save Path: %s\r\nOpen Workset Default: 3\r\nProject Spark File: 0\r\n'
            'Central Model Identity: %s\r\nLocale when saved: ENU\r\nAll Local Changes Saved To Central: 0\r\nCentral model\'s version number corresponding to the last reload latest: 1\r\n'
            'Central model\'s episode GUID corresponding to the last reload latest: %s\r\nUnique Document GUID: %s\r\nUnique Document Increments: 1\r\nModel Identity: %s\r\n'
            'IsSingleUserCloudModel: False\r\nAuthor: Autodesk Revit\r\nClientAppName: RevitApplication\r\n') % (fmt, build, path, nul, save_guid, save_guid, nul)
    t16 = text.encode('utf-16le').replace('False\r\n'.encode('utf-16le'), b'False\0' + '\r\n'.encode('utf-16le'))
    return head + b'\r\n' + t16[:-4] + b'\r\n'


# The Contents stream ends with 46 bytes after the gzip trailer that Revit validates and that depend on the exact compressed bytes (zero or recomputed
# deflate bytes are rejected; algorithm not recovered). The stream describes the GLOBAL partition only, so one Revit-written instance is reused together with its
# partition GUID (PartitionTable must carry the same GUID).
CONTENTS_GUID = '7e546952-3e9a-4f2c-b39b-bca768a3e094'
CONTENTS_STREAM = bytes.fromhex('621922051b000000010000000100000043020000000800000001000100010001000200020004000400040004000400040008000800080008000a00000000000000020000000900d8210000001000000000000062192205000000001f8b080000000000000b62656540026c40eccee0c3e0cfe0c4e008a489018c401c94195237cb4ec77ff3ec3dcb33163f98f2ef3f584a08888d180c80d898c1104c5b32c40359a660acc150c160c660c2a0c9c00e358a1988ff030133d45822c17f280866059191acf8d402000000ffff020c004227e0e6f00000000000000c28bed72ed8b0db31a569e3c9548558776796ee816ebb2964f804bc477b3cb0d1feff4555b10dc0b1a718')
