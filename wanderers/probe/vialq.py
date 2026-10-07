import os, sys, struct, lzma, json, time
dev = sys.argv[1] if len(sys.argv) > 1 else '/dev/hidraw5'
fd = os.open(dev, os.O_RDWR)
def xfer(payload):
    buf = bytes([0]) + bytes(payload) + bytes(33 - len(payload))  # report id 0 + 32 bytes
    os.write(fd, buf)
    import select
    r,_,_ = select.select([fd],[],[],6.0)
    if not r: raise TimeoutError('no reply to %r' % (payload[:4],))
    return os.read(fd, 64)
def xfer_retry(payload, n=4):
    for i in range(n):
        try: return xfer(payload)
        except TimeoutError as e:
            print('retry', i, e, file=sys.stderr)
    raise TimeoutError(payload)
# first probe: wake path
try: xfer_retry([0x01])
except TimeoutError: print('no raw HID reply after retries; keyboard halves may be asleep'); sys.exit(2)
VIA_GET_PROTOCOL=0x01; VIA_MACRO_COUNT=0x0C; VIA_MACRO_BUF=0x0D; VIA_LAYER_COUNT=0x11
VIAL=0xFE
r = xfer([VIA_GET_PROTOCOL]); print('VIA protocol', struct.unpack('>H', r[1:3])[0])
r = xfer([VIA_LAYER_COUNT]); print('dynamic layers', r[1])
r = xfer([VIA_MACRO_COUNT]); print('macro count', r[1])
r = xfer([VIA_MACRO_BUF]); print('macro buffer bytes', struct.unpack('>H', r[1:3])[0])
r = xfer([VIAL, 0x00]); print('vial protocol', struct.unpack('<I', r[0:4])[0], 'uid', r[4:12].hex())
r = xfer([VIAL, 0x01]); size = struct.unpack('<I', r[0:4])[0]; print('definition size', size)
data = b''
for i in range((size+31)//32):
    r = xfer([VIAL, 0x02] + list(struct.pack('<I', i)))
    data += r[:32]
data = data[:size]
js = lzma.decompress(data).decode()
d = json.loads(js)
import pathlib; out = str(pathlib.Path(__file__).with_name('wcorne-vial-def.json'))
open(out,'w').write(json.dumps(d, indent=1))
print('name', d.get('name'), 'vendor', d.get('vendorId'), 'product', d.get('productId'))
print('matrix', d.get('matrix'), 'lighting', d.get('lighting'))
print('keys in keymap:', sum(1 for row in d['layouts']['keymap'] for k in row if isinstance(k,str) and ',' in k and not k.startswith('e')))
print('encoders:', [k for row in d['layouts']['keymap'] for k in row if isinstance(k,str) and k.startswith('e')])
print('vial section:', json.dumps(d.get('vial'), indent=1)[:800])
print('layout labels:', d['layouts'].get('labels'))
# tap dance / combo / key override counts
r = xfer([VIAL, 0x0D, 0x00]); print('dyn-entry counts tapdance/combo/keyoverride/altrepeat', list(r[0:4]))
r = xfer([VIAL, 0x05]); print('unlock status', r[0], 'unlocked?', r[0]==1)
