from datetime import timedelta
from datetime import datetime
from typing import Union
import ass
import argparse
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('inputs', nargs='+')
parser.add_argument('--out', '-o')
parser.add_argument('--offset', default='0', help='total offset, in ms, ideally should be the same as File Indexer\'s output.')
args = parser.parse_args()

for inp in args.inputs:
    if inp.endswith('.ass'):
        assfile = inp
    elif inp.endswith('clt'):
        cltfile = inp
    else:
        raise NotImplementedError('unrecognized file type:', inp)

assert assfile and cltfile, 'need ass and clt!'

out = assfile.replace('.ass', '_cut.ass') if not args.out else args.out
offset = timedelta(milliseconds=int(args.offset))
print(f'{assfile=}')
print(f'{cltfile=}')
print(f'{offset=}')

class Fragment:
    """Fragments for each trimmed interval"""
    def __init__(self, start: float, end: float):
        self.start = timedelta(seconds=start)
        self.end = timedelta(seconds=end)
        self.real_start = timedelta(0)  # 该片段在成片中的起始时间

    @property
    def len(self):
        return self.end - self.start

    def __lt__(self, other):
        return self.start < other.start

    @staticmethod
    def str2timedelta(s):
        dt = datetime.strptime(s, '%H:%M:%S.%f')
        t = dt.time()
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
        return delta

def load_fragments(cltfile) -> list[Fragment]:
    """自动读取clt的intervals，time = frame / framerate"""
    data = ET.parse(cltfile)
    cuts = list(data.find("AllCuts"))
    framerate = float(data.find('Framerate').text)
    fragments = []
    # 读取切割资讯
    for cut in cuts:
        startframe = int(cut.find("startFrame").text)
        endframe = int(cut.find("endFrame").text)
        start = startframe / framerate
        end = endframe / framerate
        fragments.append(Fragment(start, end))

    fragments.sort()

    for i in range(len(fragments)-1):
        assert not overlaps(fragments[i], fragments[i+1]), f'overlap between fragment #{i} and #{i+1}!'

    for i in range(1, len(fragments)):
        fragments[i].real_start = fragments[i-1].real_start + fragments[i-1].len

    return fragments

def overlaps(event: Union[ass.Dialogue, Fragment], fragment: Fragment) -> bool:
    return event.start <= fragment.end and fragment.start <= event.end

def overlapsAll(event: ass.Dialogue, fragments: list[Fragment]) -> list[Fragment]:
    """find all fragments that overlaps with this event"""
    res = []
    for fragment in fragments:
        if overlaps(event, fragment):
            res.append(fragment)
    return res

def proc_ass(assfile: str, fragments: list[Fragment], out: str):
    with open(assfile, encoding='utf_8_sig') as f:
        sub = ass.parse(f)
    dialogues = [event for event in sub.events if isinstance(event, ass.Dialogue)]
    out_events = []

    for event in dialogues:
        # add global offset
        event.start += offset
        event.end += offset
        # 找到所有与event有交集的片段
        overlapped_frags = overlapsAll(event, fragments)
        # 如果没有交集则跳过
        if overlapped_frags:
            left_frag = overlapped_frags[0]
            right_frag = overlapped_frags[-1]
            # clamp time if exceeds
            event.start = max(event.start, left_frag.start)
            event.end = min(event.end, right_frag.end)
            # skip if length is zero
            if event.start == event.end:
                continue
            # compute real time
            event.start = event.start - left_frag.start + left_frag.real_start
            event.end = event.end - right_frag.start + right_frag.real_start
            out_events.append(event)

    sub.events = out_events

    with open(out, 'w', encoding='utf_8_sig') as f:
        sub.dump_file(f)

    print('\nDone! Write to', out)

def main():
    fragments = load_fragments(cltfile)
    proc_ass(assfile, fragments, out)

main()