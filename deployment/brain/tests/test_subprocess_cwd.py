"""Docker wrappers must not inherit a stale cwd; all Docker commands are fakes."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

FAKE_DOCKER = r"""import json, os, sys
from pathlib import Path
try:
    current = os.getcwd()
except OSError:
    print('fake Docker getwd: invalid inherited cwd', file=sys.stderr)
    raise SystemExit(73)
arguments = sys.argv[1:]
with Path(os.environ['FAKE_DOCKER_TRACE']).open('a') as stream:
    stream.write(json.dumps({'cwd':current, 'arguments':arguments})+'\n')
if arguments[0] == 'compose':
    for option in ('--file', '--env-file', '-f'):
        if option in arguments:
            path = Path(arguments[arguments.index(option)+1])
            assert path.is_absolute() and path.is_file(), 'Compose paths must be absolute'
    if 'exec' in arguments:
        print('65001\t20\t98800\t100\t100\t7')
    elif 'logs' in arguments:
        print('offline synthetic service log')
elif arguments[0] == 'inspect':
    print('[]' if '{{json .Mounts}}' in arguments else 'sha256:'+'1'*64)
elif arguments[0] == 'stop':
    print('a'*64)
else:
    raise SystemExit('unexpected fake Docker operation')
"""


HELPER = r"""import asyncio, json, os, shutil, subprocess, sys
from pathlib import Path
from unittest.mock import patch
from canary_brain import benchmark, runtime
from tools import m5_pilot as pilot
from tools import benchmark_gateway as gateway

base = Path(sys.argv[1]).resolve()
mode = sys.argv[2]
assert Path(shutil.which('docker')).resolve() == base/'bin/docker'
fixture = base/'fixture'
fixture.mkdir()
(fixture/'database.sql').write_text('-- synthetic only\n')
world = base/'world.otbm'
world.write_bytes(b'offline fake map')
ledger = base/'never-created-ledger.sqlite3'
experiment = benchmark.Experiment(
    name='cwd-regression', output=base/'output', fixture=fixture, world_map=world,
    budget_file=ledger, bot_id=65001,
    participants=[benchmark.Participant(name='native',kind='native')],
    game_image='sha256:'+'1'*64, database_image='sha256:'+'1'*64,
    source_revision='2'*40, expected_initial_sha256='3'*64,
)
private = base/'runtime/secrets'
private.mkdir(parents=True)
for kind in ('provider','worker','ui'):
    path = private/('litellm-'+kind+'.env')
    path.write_text('SYNTHETIC_ONLY=offline-fixture\n')
    path.chmod(0o600)
policy = base/'gateway.json'
policy.write_text('{}')
gateway_env = gateway.environment(private.parent,policy,'sha256:'+'1'*64,'2'*40)

def forbidden(*args, **kwargs):
    raise AssertionError('This regression may not use credentials/providers')
runtime.AsyncOpenAI = forbidden
runtime.read_credential = forbidden

# Only this disposable helper changes cwd. No mount or actual runtime is touched.
discard = base/'discard-cwd'
discard.mkdir()
os.chdir(discard)
discard.rmdir()
try:
    os.getcwd()
except FileNotFoundError:
    pass
else:
    raise AssertionError('The helper did not reproduce an invalid cwd')
control = subprocess.run(['docker','inspect','control'],capture_output=True,text=True)
assert control.returncode == 73 and 'invalid inherited cwd' in control.stderr

if mode == 'fixture':
    harness = benchmark.DockerFixture(experiment,base/'trial','f'*32)
    harness.prepare(experiment.participants[0])
    harness.command('config','--quiet')
    harness.start_database()
    assert harness.character() == {'id':65001,'level':20,'experience':98800,'posx':100,'posy':100,'posz':7}
    harness.stop_game()
    harness.close()
    assert 'offline synthetic service log' in (harness.directory/'services.log').read_text()
elif mode == 'pilot_identity':
    image, mounts = pilot.container_identity()
    assert image == 'sha256:'+'1'*64 and mounts == []
elif mode == 'pilot_attestation':
    async def fake_campaign(config, live):
        assert live
        harness = benchmark.DockerFixture(config,base/'attested','e'*32)
        harness.prepare(config.participants[0])
        harness.start_database()
        harness.close()
        return {'offline_fake_only':True}
    with patch.object(benchmark,'run_campaign',fake_campaign):
        assert asyncio.run(pilot.run_attested_campaign(experiment)) == {'offline_fake_only':True}
elif mode == 'gateway':
    gateway.invoke(gateway.compose('config','--quiet'),gateway_env)
    assert gateway.invoke(['inspect','--format','{{.Image}}','a'*64],gateway_env) == 'sha256:'+'1'*64
    gateway.invoke(['stop','--time','1','a'*64],gateway_env)
else:
    raise AssertionError('Unknown regression mode')

assert not ledger.exists()
rows = [json.loads(line) for line in Path(os.environ['FAKE_DOCKER_TRACE']).read_text().splitlines()]
assert rows and all(row['cwd']=='/' for row in rows)
print(json.dumps({'mode':mode,'invalid_helper_cwd_confirmed':True,'negative_control':73,'commands':rows,'real_docker_calls':0,'provider_calls':0,'ledger_created':False}))
"""


@pytest.mark.parametrize(
    "mode", ["fixture", "pilot_identity", "pilot_attestation", "gateway"]
)
def test_docker_subprocesses_use_stable_cwd_from_invalid_parent(tmp_path, mode):
    """A real child process reproduces ENOENT; its Docker CLI is Python-only."""
    directory = tmp_path / "bin"
    directory.mkdir()
    docker = directory / "docker"
    docker.write_text("#!" + sys.executable + "\n" + FAKE_DOCKER)
    docker.chmod(0o700)
    helper = tmp_path / "invalid_cwd_helper.py"
    helper.write_text(HELPER)
    brain = Path(__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "PATH": str(directory) + os.pathsep + os.environ.get("PATH", ""),
        "PYTHONPATH": str(brain / "src") + os.pathsep + str(brain),
        "PYTHONDONTWRITEBYTECODE": "1",
        "FAKE_DOCKER_TRACE": str(tmp_path / "fake-docker-trace.jsonl"),
    }
    result = subprocess.run(
        [sys.executable, str(helper), str(tmp_path), mode],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["invalid_helper_cwd_confirmed"] and report["negative_control"] == 73
    assert report["real_docker_calls"] == 0 and report["provider_calls"] == 0
    assert not report["ledger_created"]
    calls = [row["arguments"] for row in report["commands"]]
    if mode == "fixture":
        assert any("config" in args and "--quiet" in args for args in calls)
        assert any("stop" in args for args in calls)
        assert any("exec" in args for args in calls)
        assert any("logs" in args for args in calls)
        assert any("down" in args for args in calls)
    elif mode == "pilot_identity":
        assert len(calls) == 2 and all(args[0] == "inspect" for args in calls)
    elif mode == "pilot_attestation":
        assert any(args[0] == "inspect" and args[-1] == "{{.Image}}" for args in calls)
    else:
        assert any(args[0] == "stop" for args in calls)
