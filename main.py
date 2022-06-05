#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PICO_LANG = 'es-ES'
TESSERACT_LANG = 'spa'
# I'm not sure what's pico2wave's maximum length, empirically looked for a decent value
MAX_LENGTH = 20000

pdf = sys.stdin.buffer.read()
process = subprocess.Popen(('pdfinfo', '-meta', '-'), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
process.stdin.write(pdf)

out = process.communicate()[0].decode('utf-8')

title = ''
author = ''

if out != '':
    root = ET.fromstring(out)
    try:
        title = root.findall('.//dc:title//rdf:li', {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        })[0].text
    except:
        pass

    try:
        author = root.findall('.//dc:creator//rdf:li', {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        })[0].text
    except:
        pass


process = subprocess.Popen(('pdftotext', '-nopgbrk', '-', '-'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
process.stdin.write(pdf)
output = process.communicate()[0].decode('utf-8')

def chunk_output(output):
    outputs = ['']
    buf = ''
    for line in output.split('\n'):
        line = line.strip()
        if len(line) == 0:
            continue

        if line[-1:] == '-':
            buf = line[:-1]
        else:
            add = buf + line + ' '
            if len(add + outputs[len(outputs)-1]) > MAX_LENGTH:
                outputs.append('')
            outputs[len(outputs)-1] += add
            buf = ''
    return outputs

if len(output) == 0:
    htmldir = tempfile.mkdtemp()
    process = subprocess.Popen((
        'pdftohtml',
        '-c',
        '-',
        os.path.join(htmldir, 'pdfdoc'),
    ), stdin=subprocess.PIPE)
    process.stdin.write(pdf)
    process.communicate()

    for root, dirs, files in os.walk(htmldir):
        for name in sorted(files):
            if not name.endswith('.png') and not name.endswith('.jpg'):
                continue
            out = subprocess.check_output(('tesseract', '-l', TESSERACT_LANG, os.path.join(root, name), '-'))
            output += out.decode('utf-8') + ' '
    shutil.rmtree(htmldir)

outputs = chunk_output(output)
with tempfile.NamedTemporaryFile(suffix='playlist.txt', mode='w', encoding='utf-8') as playlist:
    wavs = []
    for chunk in outputs:
        wav = os.path.join(tempfile.mkdtemp(), 'audio.wav')
        subprocess.check_call(('pico2wave', '-l', PICO_LANG, '-w', wav, '--') + (chunk,))
        wavs.append(wav)
        playlist.write("file '")
        playlist.write(wav)
        playlist.write("'\n")
    playlist.flush()

    subprocess.check_call((
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', playlist.name,
        '-f', 'mp3',
        '-metadata', f'artist="{author}"',
        '-metadata', f'title="{title}"',
        '-',
    ))

for wav in wavs:
    os.unlink(wav)
