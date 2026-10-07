#!/usr/bin/env python3
"""Robust Vial raw-HID probe for the W-Corne 2.4G dongle.

The dongle relays Vial requests to the keyboard over the radio and answers
with 0xFF filler when the keyboard does not reply in time, so every request
is retried until a reply echoes the command byte with real content.
Logs progress to stdout; writes the embedded definition next to this file.
"""
import os, sys, struct, lzma, json, time, select, glob, pathlib

DEADLINE = float(sys.argv[1]) if len(sys.argv) > 1 else 240.0   # seconds overall
VIA_GET_PROTOCOL, VIA_GET_KB_VALUE, VIA_MACRO_COUNT, VIA_MACRO_BUF, VIA_LAYER_COUNT = 0x01, 0x02, 0x0C, 0x0D, 0x11
VIAL = 0xFE
t0 = time.time()
def log(*a): print('%6.1f' % (time.time() - t0), *a, flush=True)

def find_node():
    c = glob.glob('/dev/input/by-id/usb-Pilot_W-CORNE_vial*-if01-hidraw')
    return os.path.realpath(c[0]) if c else None

fd = None
def ensure_fd():
    global fd
    if fd is not None:
        try: os.fstat(fd); return True
        except OSError: fd = None
    n = find_node()
    if n and os.access(n, os.R_OK | os.W_OK):
        fd = os.open(n, os.O_RDWR | os.O_NONBLOCK); log('opened', n); return True
    return False

def drain():
    while True:
        r, _, _ = select.select([fd], [], [], 0)
        if not r: return
        try: os.read(fd, 64)
        except OSError: return

def xfer(payload, valid, wait=2.0):
    """Send once; return first reply passing valid(), or None."""
    buf = bytes([0]) + bytes(payload) + bytes(32 - len(payload))
    try:
        os.write(fd, buf)
    except OSError as e:
        log('write err', e.errno); return None
    end = time.time() + wait
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], max(0, end - time.time()))
        if not r: break
        try: data = os.read(fd, 64)
        except OSError as e: log('read err', e.errno); return None
        if valid(data): return data
    return None

def ask(payload, valid, label):
    tries = 0
    while time.time() - t0 < DEADLINE:
        if not ensure_fd(): time.sleep(0.5); continue
        drain()
        r = xfer(payload, valid)
        tries += 1
        if r is not None:
            log(label, 'ok after', tries, 'tries'); return r
        if tries % 10 == 0: log(label, 'still waiting,', tries, 'tries')
        time.sleep(0.3)
    log(label, 'GAVE UP'); sys.exit(2)

echo = lambda cmd: (lambda d: d[0] == cmd and d[1:3] != b'\xff\xff')
r = ask([VIA_GET_PROTOCOL], echo(VIA_GET_PROTOCOL), 'via protocol'); log('VIA protocol', struct.unpack('>H', r[1:3])[0])
r = ask([VIA_LAYER_COUNT], lambda d: d[0] == VIA_LAYER_COUNT and d[1] not in (0, 0xff), 'layer count'); log('dynamic layers', r[1])
r = ask([VIA_MACRO_COUNT], lambda d: d[0] == VIA_MACRO_COUNT and d[1] != 0xff, 'macro count'); log('macro count', r[1])
r = ask([VIA_MACRO_BUF], echo(VIA_MACRO_BUF), 'macro buffer'); log('macro buffer bytes', struct.unpack('>H', r[1:3])[0])
r = ask([VIA_GET_KB_VALUE, 0x04], lambda d: d[0] == VIA_GET_KB_VALUE and d[1] == 0x04, 'fw version'); log('VIA firmware version', struct.unpack('>I', r[2:6])[0])
r = ask([VIAL, 0x00], lambda d: d[:4] != b'\xff\xff\xff\xff' and d[:4] != b'\x00\x00\x00\x00', 'vial id'); log('vial protocol', struct.unpack('<I', r[0:4])[0], 'uid', r[4:12].hex())
r = ask([VIAL, 0x01], lambda d: 0 < struct.unpack('<I', d[0:4])[0] < 65536, 'def size'); size = struct.unpack('<I', r[0:4])[0]; log('definition size', size)
chunks = (size + 31) // 32; data = b''
for i in range(chunks):
    r = ask([VIAL, 0x02] + list(struct.pack('<I', i)), lambda d: d != b'\xff' * 32 or i > 0, 'chunk %d/%d' % (i + 1, chunks) if i % 10 == 0 or i == chunks - 1 else 'chunk')
    data += r[:32]
data = data[:size]
try:
    d = json.loads(lzma.decompress(data).decode())
except Exception as e:
    log('definition decode failed:', e); pathlib.Path(__file__).with_name('wcorne-vial-def.bin').write_bytes(data); sys.exit(3)
out = pathlib.Path(__file__).with_name('wcorne-vial-def.json'); out.write_text(json.dumps(d, indent=1))
log('definition saved to', out)
log('name', d.get('name'), 'matrix', d.get('matrix'))
keys = [k for row in d['layouts']['keymap'] for k in row if isinstance(k, str) and ',' in k]
log('keys', len(keys), 'encoders', [k for k in keys if k.startswith('e')])
log('vial section', json.dumps(d.get('vial'))[:600])
r = ask([VIAL, 0x0D, 0x00], lambda d: d != b'\xff' * 32, 'dynamic entries'); log('tapdance/combo/keyoverride/altrepeat slots', list(r[0:4]))
r = ask([VIAL, 0x05], lambda d: d[0] in (0, 1), 'unlock status'); log('unlocked', r[0] == 1)
log('DONE')
