from pathlib import Path
import shutil
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';shutil.copy2(p,r/'neighbors29-before-mon.c');s=p.read_text()
a='''    int maxx, maxy;
''';b='''    static const signed char dx[8] = { -1, -1, -1, 0, 0, 1, 1, 1 };
    static const signed char dy[8] = { -1, 0, 1, -1, 1, -1, 0, 1 };
    int neighbor;
''';assert s.count(a)==1;s=s.replace(a,b)
a='''    maxx = min(x + 1, COLNO - 1);
    maxy = min(y + 1, ROWNO - 1);
    for (nx = max(1, x - 1); nx <= maxx; nx++)
        for (ny = max(0, y - 1); ny <= maxy; ny++) {
            if (nx == x && ny == y)
                continue;'''
b='''    for (neighbor = 0; neighbor < 8; neighbor++) {
            nx = x + dx[neighbor];
            ny = y + dy[neighbor];
            if (nx < 1 || nx >= COLNO || ny < 0 || ny >= ROWNO)
                continue;'''
assert s.count(a)==1;p.write_text(s.replace(a,b))
