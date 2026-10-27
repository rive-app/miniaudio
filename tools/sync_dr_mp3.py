#!/usr/bin/env python3
# Embeds a dr_libs dr_mp3.h in miniaudio.h and the split build the way
# miniaudio does: renamed, comments and blank lines stripped, and the blocks
# miniaudio defines itself dropped. Usage: tools/sync_dr_mp3.py dr_mp3.h
import re, sys, os

src = open(sys.argv[1]).read()
h0 = src.index('#ifndef dr_mp3_h')
h1 = src.index('#endif  /* dr_mp3_h */') + len('#endif  /* dr_mp3_h */')
c0 = src.index('#if defined(DR_MP3_IMPLEMENTATION)', h1)
c1 = src.index('#endif  /*DR_MP3_IMPLEMENTATION*/')
header, impl = src[h0:h1], src[c0:c1]

def drop_blocks(s):
    for name in ['Sized Types', 'Decorations', 'Result Codes', 'Inline', 'Allocation Callbacks', 'SIZE_MAX', 'Errno', 'fopen']:
        s = re.sub(r'/\* ' + name + r' \*/.*?/\* End ' + name + r' \*/', '', s, flags=re.S)
    return s
header, impl = drop_blocks(header), drop_blocks(impl)

def strip_comments(s):
    out, i, n = [], 0, len(s)
    while i < n:
        if s.startswith('/*', i):
            j = s.index('*/', i + 2) + 2
            i = j
            continue
        if s.startswith('//', i):
            j = s.find('\n', i)
            i = n if j < 0 else j
            continue
        if s[i] in '"\'':
            q = s[i]; j = i + 1
            while s[j] != q:
                j += 2 if s[j] == '\\' else 1
            out.append(s[i:j + 1]); i = j + 1
            continue
        out.append(s[i]); i += 1
    return ''.join(out)

def rename(s):
    for t in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64', 'uintptr', 'bool8', 'bool32']:
        s = re.sub(r'\bdrmp3_' + t + r'\b', 'ma_' + t, s)
    s = re.sub(r'\bdrmp3_result\b', 'ma_result', s)
    s = re.sub(r'\bDRMP3_INLINE\b', 'MA_INLINE', s)
    s = re.sub(r'\bdrmp3_result_from_errno\b', 'ma_result_from_errno', s)
    s = re.sub(r'\bdrmp3_fopen\b', 'ma_fopen', s)
    s = re.sub(r'\bdrmp3_wfopen\b', 'ma_wfopen', s)
    for code in re.findall(r'#define DRMP3_([A-Z_]+)\s+-?\d+', src[src.index('/* Result Codes */'):src.index('/* End Result Codes */')]):
        s = re.sub(r'\bDRMP3_' + code + r'\b', 'MA_' + code, s)
    s = re.sub(r'\bDRMP3_TRUE\b', 'MA_TRUE', s)
    s = re.sub(r'\bDRMP3_FALSE\b', 'MA_FALSE', s)
    s = re.sub(r'\bDRMP3_API\b', 'MA_API', s)
    s = re.sub(r'\bDRMP3_PRIVATE\b', 'MA_PRIVATE', s)
    s = re.sub(r'\bdrmp3_allocation_callbacks\b', 'ma_allocation_callbacks', s)
    s = re.sub(r'\bdr_mp3_h\b', 'ma_dr_mp3_h', s)
    s = re.sub(r'\bdr_mp3_c\b', 'ma_dr_mp3_c', s)
    s = re.sub(r'\bg_drmp3_', 'ma_dr_mp3_g_', s)
    s = re.sub(r'\bDRMP3_UINT64_MAX\b', 'MA_UINT64_MAX', s)
    s = re.sub(r'\bDRMP3_SIZE_MAX\b', 'MA_SIZE_MAX', s)
    s = re.sub(r'\bdrmp3', 'ma_dr_mp3', s)
    s = re.sub(r'\bDRMP3', 'MA_DR_MP3', s)
    s = re.sub(r'\bDR_MP3_', 'MA_DR_MP3_', s)
    return s

def clean(s):
    lines = [l.rstrip() for l in strip_comments(s).split('\n')]
    return '\n'.join(l for l in lines if l.strip()) + '\n'

impl = impl[impl.index('\n') + 1:]
h, c = rename(clean(header)), rename(clean(impl))

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
for path in ('miniaudio.h', 'extras/miniaudio_split/miniaudio.h', 'extras/miniaudio_split/miniaudio.c'):
    path = os.path.join(root, path)
    s = open(path).read()
    for begin, end, section in (('/* dr_mp3_h begin */\n', '/* dr_mp3_h end */', h),
                                ('/* dr_mp3_c begin */\n', '/* dr_mp3_c end */', c)):
        if begin in s:
            a = s.index(begin) + len(begin)
            s = s[:a] + section + s[s.index(end, a):]
    open(path, 'w').write(s)
