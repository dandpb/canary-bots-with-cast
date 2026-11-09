#!/usr/bin/env python3
"""Live SQL-barrier regression on the labelled disposable lifecycle stack only."""
import json
import sys
import time

import lifecycle_qa as q


def sql(query):
    q.verify(q.PREFIX+'-db')
    return q.docker('exec', q.PREFIX+'-db', 'mariadb', '-uroot', '-plifecycle-qa-only', '-N', 'canary', '-e', query)

def row():
    fields = sql('SELECT experience,skill_sword,skill_sword_tries FROM players WHERE id=65001').split('\t')
    attrs = sql('SELECT HEX(attributes) FROM player_items WHERE player_id=65001 AND itemtype=28540')
    return dict(xp=int(fields[0]), skill=int(fields[1]), tries=int(fields[2]), attributes=attrs)

q.command('brain', operation='disable')
if any(bot['guid'] == 65001 and bot['hibernated'] for bot in q.command('roster')):
    q.command('wake')
q.command('load')
before = q.command('mutate', value=1701, charges=77)
sql('DROP TRIGGER IF EXISTS qa_snapshot_gate')
sql('CREATE TRIGGER qa_snapshot_gate BEFORE UPDATE ON players FOR EACH ROW SET @qa_snapshot_delay=IF(NEW.id=65001,SLEEP(5),0)')
try:
    q.command('hibernate')
    deadline=time.monotonic()+8
    while sql("SELECT COUNT(*) FROM information_schema.processlist WHERE STATE='User sleep'")=='0':
        assert time.monotonic()<deadline, 'worker did not reach deterministic SQL barrier'
        time.sleep(.05)
    started=time.monotonic()
    q.command('wake')
    after=q.command('mutate', value=1702, charges=66)
    if '--reload' in sys.argv:
        identity = sorted((bot['guid'], bot['runtimeId']) for bot in q.command('roster'))
        assert q.command('reload')['ok']
        assert sorted((bot['guid'], bot['runtimeId']) for bot in q.command('roster')) == identity
        after=q.command('mutate', value=1703, charges=55)
    control=time.monotonic()-started
    time.sleep(max(0,5.5-control))
    persisted=row()
    print(json.dumps(dict(before=before,after=after,persisted=persisted,control_seconds=control)),flush=True)
    expected='164D00'
    coherent=(persisted['skill'],persisted['tries'])==(before['skill'],before['tries']) and expected in persisted['attributes']
    if '--expect-mixed' in sys.argv:
        assert not coherent and '164200' in persisted['attributes'], persisted
        print('REPRODUCED mixed old skills + newly mutated item charges',flush=True)
    else:
        assert coherent, 'SQL worker read fields changed after the checkpoint capture'
        print('PASS SQL checkpoint stays coherent during wake and live mutation',flush=True)
finally:
    sql('DROP TRIGGER IF EXISTS qa_snapshot_gate')
q.command('hibernate')
time.sleep(2)
final=row()
assert (final['skill'],final['tries'])==(after['skill'],after['tries']), final
assert ('163700' if '--reload' in sys.argv else '164200') in final['attributes'], final
print('PASS next checkpoint persists the latest skills and charges',flush=True)
