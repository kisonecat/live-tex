import fileinput
import time
import re
import math

announce_buffer = "%%%buffer%%%\n"
end_buffer = "%%%EOF%%%\n"

lines = []
point = 1
mark = 1
for line in fileinput.input():
    x = re.match('^%%%point ([0-9]+) mark ([0-9]+)$', line)
    if x:
        point = x.groups()[0]
        mark = x.groups()[1]
    elif line == announce_buffer:
        lines = []
    elif line == end_buffer:
        t = math.floor(time.time()*1000)
        f = open('board{:013d}.tex'.format(t), 'w')
        f.write(''.join(lines))
        f.close()
        lines = []

        f = open('point{:013d}.txt'.format(t), 'w')
        f.write(str(point))
        f.close()                
    else:
        lines.append(line)

