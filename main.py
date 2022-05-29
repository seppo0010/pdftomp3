#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile

# I'm not sure what's pico2wave's maximum length, empirically looked for a decent value
MAX_LENGTH = 20000

process = subprocess.Popen(('pdftotext', '-nopgbrk', '-', '-'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
process.stdin.write(sys.stdin.buffer.read())

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

    subprocess.check_call(('ffmpeg', '-f', 'concat', '-safe', '0', '-i', playlist.name, '-f', 'mp3', '-'))

for wav in wavs:
    os.unlink(wav)
