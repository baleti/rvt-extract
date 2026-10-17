"""File-level extractors (OLE streams, materials). Each takes the project path and returns (json_data, [(relative_path, bytes)])."""
import io, re, zipfile
import olefile
import xml.etree.ElementTree as ET


def _u16(d):
    best = ''
    for a in (0, 1):
        t = d[a:].decode('utf-16le', 'ignore')
        if len(re.findall(r'[A-Za-z]{4,}', t)) > len(re.findall(r'[A-Za-z]{4,}', best)): best = t
    return best


def project_info(path):
    o = olefile.OleFileIO(path); out = {}
    t = _u16(o.openstream('BasicFileInfo').read())
    for k in ('Format', 'Build', 'Last Save Path', 'Worksharing', 'Username', 'Central Model Path', 'Open Workset Default', 'Locale when saved', 'Central Model Identity'):
        m = re.search(re.escape(k) + r':[ \t]*([^\r\n]*)', t)
        if m: out[k.lower().replace(' ', '_')] = m.group(1).strip()
    out['basic_file_info_text'] = t.replace('\x00', '').strip()[:4000]
    if o.exists('ProjectInformation'):
        try:
            z = zipfile.ZipFile(io.BytesIO(o.openstream('ProjectInformation').read())); x = z.read(z.namelist()[0]).decode('utf-8', 'ignore')
            m = re.search(r'<title>(.*?)</title>', x); out['title'] = m and m.group(1)
            m = re.search(r'<A:product-version>(.*?)</A:product-version>', x); out['product_version'] = m and m.group(1)
            out['project_information_xml'] = x
        except Exception as e: out['project_information_error'] = str(e)
    files = []
    if o.exists('RevitPreview4.0'):
        d = o.openstream('RevitPreview4.0').read(); i = d.find(b'\x89PNG')
        if i >= 0: files.append(('preview.png', d[i:]))
    return out, files


def links(path):
    o = olefile.OleFileIO(path)
    if not o.exists('TransmissionData'): return [], []
    d = o.openstream('TransmissionData').read(); t = _u16(d); i = t.find('<TransmissionData')
    out = []
    try:
        root = ET.fromstring(t[i:t.rfind('>') + 1])
        for e in root.iter('ExternalFileReference'):
            out.append({c.tag: (c.text or '') for c in e})
    except Exception as e:
        out.append({'error': str(e)})
    return out, [('transmission_data.xml', t[i:].encode('utf-8'))]


def materials(path):
    import rvt_materials as M
    tab = M.material_table(path)
    return list(tab.values()), []


KINDS = {'project_info': project_info, 'links': links, 'materials': materials}
