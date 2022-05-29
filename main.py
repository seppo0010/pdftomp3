#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

# I'm not sure what's pico2wave's maximum length, empirically looked for a decent value
MAX_LENGTH = 20000

pdf = sys.stdin.buffer.read()
process = subprocess.Popen(('pdfinfo', '-meta', '-'), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
process.stdin.write(pdf)

out = process.communicate()[0].decode('utf-8')

root = ET.fromstring(out)

title = ''
try:
    title = root.findall('.//dc:title//rdf:li', {
        'dc': 'http://purl.org/dc/elements/1.1/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    })[0].text
except:
    pass

author = ''
try:
    author = root.findall('.//dc:creator//rdf:li', {
        'dc': 'http://purl.org/dc/elements/1.1/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    })[0].text
except:
    pass


process = subprocess.Popen(('pdftotext', '-nopgbrk', '-', '-'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
process.stdin.write(pdf)

outputs = ['']
buf = ''
for line in process.communicate()[0].decode('utf-8').split('\n'):
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

with tempfile.NamedTemporaryFile(suffix='playlist.txt', mode='w', encoding='utf-8') as playlist:
    wavs = []
    for output in outputs:
        wav = os.path.join(tempfile.mkdtemp(), 'audio.wav')
        subprocess.check_call(('pico2wave', '-l', 'es-ES', '-w', wav, '--') + (output,))
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
