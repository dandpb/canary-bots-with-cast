"""Offline tests of the managed return of one quiescent attempt. Docker and every mutation are mocked."""

import fcntl
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import qa_return_attempt as ret
import stage2_handoff as handoff
import test_stage2_handoff as base

GAME, BRAIN = base.GAME, base.BRAIN
RESCUE, CANDIDATE = base.RESCUE, base.CANDIDATE
MANAGED = ret.MANAGED
sha = base.sha


def forbidden(*args, **kwargs):
    raise AssertionError(f"a real subprocess was started in an offline test: {args!r}")


class ReturnAttemptTests(base.QuiescentTests):
    """The return over the adapter's own fake host: a real quiescent stop, then the return."""

    def setUp(self):
        super().setUp()
        import preflight

        preflight.command.side_effect = self.command
        handoff.execute.side_effect = self.run_up
        self.mutations = []
        self.slept = []
        rescue_config = self.manifest["rescue_container_config"]["config_sha256"]
        for mock in (
            patch.object(ret, "MANIFEST_SHA256", sha(self.manifest_path.read_bytes())),
            patch.object(ret, "RESCUE_CONFIG_SHA256", rescue_config),
            patch.object(
                ret,
                "RESCUE_RESULT_SHA256",
                sha(self.receipts["rescue_result"].read_bytes()),
            ),
            patch.object(ret, "run_mutation", side_effect=self.mutation),
            patch("stage1_baseline.playable", return_value=[]),
            patch("subprocess.run", side_effect=forbidden),
        ):
            self.stack.enter_context(mock)
        self.legacy = self.project / ret.CLAIM_ROOT
        self.legacy.mkdir(parents=True)
        self.legacy.chmod(0o700)
        for name, text in (
            ("flow.lock", ""),
            ("stop-rescue.claim", '{"step": "stop-rescue"}\n'),
            ("stop-rescue.result", '{"exit_code": 0, "step": "stop-rescue"}\n'),
            ("start-managed.claim", '{"step": "start-managed"}\n'),
            ("start-managed.result", '{"exit_code": 0, "step": "start-managed"}\n'),
        ):
            path = self.legacy / name
            path.write_text(text)
            path.chmod(0o600)
        self.legacy_state = self.snapshot_legacy()
        self.receipt_state = self.snapshot(self.receipts["rescue_result"])

    def tearDown(self):
        # every test: the 03:33 claims and the historical receipt stay byte-identical, untouched
        self.assertEqual(self.snapshot_legacy(), self.legacy_state)
        self.assertEqual(
            self.snapshot(self.receipts["rescue_result"]), self.receipt_state
        )
        super().tearDown()

    @staticmethod
    def snapshot(path):
        info = os.lstat(path)
        return path.read_bytes(), stat.S_IMODE(info.st_mode), info.st_mtime_ns

    def snapshot_legacy(self):
        return {
            p.name: self.snapshot(p)
            for p in sorted(self.legacy.iterdir())
            if p.is_file()
        }

    # -- the fake host -------------------------------------------------------------------------

    def ownership(self):
        files = ",".join(
            self.manifest["bundle_files"][name]["absolute_path"]
            for name in handoff.COMPOSE_FILES
        )
        return {
            "com.docker.compose.project.working_dir": str(self.project),
            "com.docker.compose.project.config_files": files,
            "com.docker.compose.project.environment_file": self.manifest[
                "env_file_path"
            ],
            "com.docker.compose.oneoff": "False",
        }

    def command(self, *args, env=None):
        if args[1] == "inspect" and args[-1] == ret.NEW_INSPECT:
            item = self.docker.find(args[2])
            if not item:
                raise RuntimeError("read-only command failed: docker inspect")
            return json.dumps(
                {
                    **{k: item[k] for k in ("id", "created_at", "image_id", "status")},
                    "restart": item.get("restart", "no"),
                    "name": "/" + item["name"],
                    "labels": item["labels"],
                }
            )
        return self.docker(*args, env=env)

    def run_up(self, argv):
        """The adapter's mocked up, with the Compose ownership labels a real up writes."""
        out = self.docker.run(argv)
        if "up" in argv:
            for name in (GAME, BRAIN):
                item = self.docker.containers[name]
                item["labels"] = {**item["labels"], **self.ownership()}
        return out

    def mutation(self, argv, timeout, keep):
        lock = self.attempt_dir(self.key) / ret.LOCK
        self.mutations.append((argv, timeout, keep, self.lock_is_busy(lock)))
        code, out, err = self.docker.run(argv)
        return code, out.encode(), err.encode()

    def sleep(self, seconds):
        """Time passes: a started container gets a fresh healthy check."""
        self.slept.append(seconds)
        for item in [*self.docker.containers.values(), *self.docker.others.values()]:
            if item.get("health") == "starting":
                end = datetime.fromisoformat(item["started_at"]) + timedelta(seconds=20)
                item.update(
                    health="healthy",
                    health_log=[{"End": end.isoformat(), "ExitCode": 0}],
                )

    @staticmethod
    def lock_is_busy(path):
        descriptor = os.open(path, os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        finally:
            os.close(descriptor)
        return False

    # -- helpers -------------------------------------------------------------------------------

    def stopped_attempt(self):
        """A real quiescent pre-stop and its exec-step stop: the attempt key is the pre-stop sha."""
        path, key = self.q_pre_stop()
        self.new().exec_step(path, key)
        self.key = key
        return key

    def partial_up(self):
        """The whole quiescent chain, then an up that fails half way (game recreated, brain created)."""
        bundle, digest = self.q_bundled()[0]
        self.docker.up_fails = True
        with self.assertRaisesRegex(RuntimeError, "HOLD"):
            self.new().exec_step(bundle, digest)
        claims = self.project / handoff.CLAIMS
        self.key = next(claims.glob("*.quiescent-stop-game.claim")).name.split(".")[0]
        return self.key

    def attempt(self, key=None, notice_sha=None):
        return ret.ReturnAttempt(
            handoff,
            self.new(),
            key or self.key,
            self.notice,
            notice_sha or sha(self.notice.read_bytes()),
            sleep=self.sleep,
        )

    def attempt_dir(self, key):
        return self.project / ret.ATTEMPTS / key

    def starts(self, ident):
        return sum(run == ["docker", "start", ident] for run in self.docker.runs)

    # -- Branch A ------------------------------------------------------------------------------

    def test_branch_a_starts_the_managed_original_once_and_abandons_the_up(self):
        key = self.stopped_attempt()
        done = self.attempt().start_managed()
        self.assertEqual(done["branch"], "A")
        self.assertEqual(self.docker.runs[-1], ["docker", "start", MANAGED])
        self.assertEqual(self.starts(MANAGED), 1)
        self.assertEqual(self.docker.find(MANAGED)["status"], "running")
        directory = self.attempt_dir(key)
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        for name in (ret.ABANDONED, "start-managed.claim", "start-managed.result"):
            self.assertEqual(
                stat.S_IMODE((directory / name).stat().st_mode), 0o600, name
            )
        marker = json.loads((directory / ret.ABANDONED).read_text())
        self.assertEqual(marker["attempt"], key)
        claim = json.loads((directory / "start-managed.claim").read_text())
        self.assertEqual(claim["argv"], ["docker", "start", MANAGED])
        self.assertEqual(claim["timeout_seconds"], ret.START_TIMEOUT)
        gate = Path(claim["gate"]["path"])
        self.assertEqual(sha(gate.read_bytes()), claim["gate"]["sha256"])
        bound = json.loads(gate.read_text())
        self.assertEqual(bound["manifest_sha256"], ret.MANIFEST_SHA256)
        self.assertEqual(bound["adapter"]["sha256"], sha(base.ADAPTER))
        stop = json.loads(
            (
                self.project / handoff.CLAIMS / f"{key}.quiescent-stop-game.result"
            ).read_text()
        )
        self.assertEqual(bound["stop_claim"]["exec_step_sha256"], stop["sha256"])
        self.assertEqual(
            bound["window_notice"]["sha256"], sha(self.notice.read_bytes())
        )
        self.assertEqual(bound["managed"]["id"], MANAGED)
        self.assertEqual(bound["gate"]["db_writers"]["other_sessions"], 0)
        self.assertEqual(bound["gate"]["db_integrity"], "ok")
        argv, timeout, keep, busy = self.mutations[-1]
        self.assertEqual(
            (argv, timeout), (["docker", "start", MANAGED], ret.START_TIMEOUT)
        )
        self.assertEqual(len(keep), 1)  # the lock goes to the mutation's child
        self.assertTrue(busy)  # held for the whole mutation
        self.assertEqual(done["result"], "pass")
        self.assertEqual(done["health"]["health"], "healthy")
        self.assertTrue(self.slept)  # it waited for a check newer than the start
        with self.assertRaisesRegex(
            RuntimeError, "HOLD: start-managed.claim is consumed"
        ):
            self.attempt().start_managed()
        with self.assertRaisesRegex(RuntimeError, "Branch A ran"):
            self.attempt().rescue()
        self.assertEqual(self.starts(MANAGED), 1)
        self.assertFalse(self.lock_is_busy(directory / ret.LOCK))

    def setting(self, find, **values):
        """A change to a fake container and its exact undo (only those keys)."""
        before = {}

        def change():
            item = find()
            before.update({key: item.get(key) for key in values})
            item.update(values)

        def undo():
            find().update(before)

        return change, undo

    def test_branch_a_refusals_start_nothing(self):
        key = self.stopped_attempt()
        game = lambda: self.docker.containers[GAME]
        held = {}

        def missing():
            held["game"] = self.docker.containers.pop(GAME)

        def back():
            self.docker.containers[GAME] = held["game"]

        def config():
            game()["env"] = [*game()["env"], "EXTRA=1"]

        def config_back():
            game()["env"] = game()["env"][:-1]

        def writer():
            self.docker.writers = 1

        def no_writer():
            self.docker.writers = 0

        def transaction():
            self.docker.probe["trx"] = [["24116", "RUNNING", "0"]]

        def no_transaction():
            self.docker.probe["trx"] = []

        def integrity():
            self.docker.integrity["check"]["players"] = "corrupt"

        def integrity_back():
            self.docker.integrity["check"]["players"] = "OK"

        up = self.project / handoff.CLAIMS / f"{'c' * 64}.quiescent-up.claim"

        def up_claimed():
            when = (self.clock.now + timedelta(seconds=5)).isoformat()
            up.write_text(json.dumps({"claimed_at_utc": when}) + "\n")

        def rescue(**values):
            return self.setting(lambda: self.docker.find(RESCUE), **values)

        def candidate(**values):
            return self.setting(lambda: self.docker.find(CANDIDATE), **values)

        cases = (
            ("missing", (missing, back), "managed original eaae6fe2171b is absent"),
            (
                "created_at",
                self.setting(game, created_at="2026-11-08T00:06:00Z"),
                "changed since the pre-stop \\(created_at\\)",
            ),
            (
                "config",
                (config, config_back),
                "changed since the pre-stop \\(config_sha256\\)",
            ),
            ("exit code", self.setting(game, exit_code=137), "not stopped with exit 0"),
            (
                "restarted",
                self.setting(game, started_at="2026-11-08T01:00:00Z"),
                "started again since the quiescent stop",
            ),
            ("rescue running", rescue(status="running"), "must be stopped"),
            ("candidate running", candidate(status="running"), "must be stopped"),
            ("writer", (writer, no_writer), "other connection"),
            ("transaction", (transaction, no_transaction), "1 transaction"),
            ("integrity", (integrity, integrity_back), "CHECK TABLE is not OK"),
            (
                "up attempted",
                (up_claimed, up.unlink),
                "start-managed is closed; use the rescue",
            ),
        )
        for name, (change, undo), message in cases:
            with self.subTest(name):
                change()
                try:
                    with self.assertRaisesRegex(RuntimeError, message):
                        self.attempt().start_managed()
                finally:
                    undo()
                self.assertFalse(
                    (self.attempt_dir(key) / "start-managed.claim").exists()
                )
        self.assertEqual(self.starts(MANAGED), 0)
        self.assertTrue(
            (self.attempt_dir(key) / ret.ABANDONED).is_file()
        )  # abandoned anyway
        self.attempt().start_managed()  # the gates pass again: a refusal consumed nothing
        self.assertEqual(self.starts(MANAGED), 1)

    def test_branch_a_post_claim_revalidation_holds_without_mutation(self):
        key = self.stopped_attempt()
        original = ret.ReturnAttempt.gate_managed

        def gate_then_drift(attempt):
            gate = original(attempt)
            self.docker.find(CANDIDATE)["status"] = "running"
            return gate

        with (
            patch.object(ret.ReturnAttempt, "gate_managed", gate_then_drift),
            self.assertRaisesRegex(
                RuntimeError, "HOLD: the state changed after the claim"
            ),
        ):
            self.attempt().start_managed()
        result = json.loads(
            (self.attempt_dir(key) / "start-managed.result").read_text()
        )
        self.assertFalse(result["executed"])
        self.assertEqual(self.starts(MANAGED), 0)
        self.docker.find(CANDIDATE)["status"] = "exited"
        with self.assertRaisesRegex(RuntimeError, "consumed .*executed False"):
            self.attempt().start_managed()
        self.assertEqual(self.starts(MANAGED), 0)

    def test_branch_a_unhealthy_start_holds_and_is_never_replayed(self):
        key = self.stopped_attempt()

        def unhealthy(seconds):
            self.docker.find(MANAGED)["health"] = "unhealthy"

        attempt = self.attempt()
        attempt.sleep = unhealthy
        with self.assertRaisesRegex(
            RuntimeError, "HOLD: eaae6fe2171b has no healthy check"
        ):
            attempt.start_managed()
        records = sorted(self.attempt_dir(key).glob("verify-start-managed-*.json"))
        self.assertEqual(json.loads(records[0].read_text())["result"], "hold")
        with self.assertRaisesRegex(RuntimeError, "consumed \\(exit 0"):
            self.attempt().start_managed()
        self.assertEqual(self.starts(MANAGED), 1)

    def test_branch_a_smoke_failure_holds(self):
        self.stopped_attempt()
        with (
            patch(
                "stage1_baseline.playable",
                return_value=["game: 127.0.0.1:17171 is not listening"],
            ),
            self.assertRaisesRegex(RuntimeError, "HOLD: the smoke check failed"),
        ):
            self.attempt().start_managed()
        self.assertEqual(self.starts(MANAGED), 1)

    # -- Branch B ------------------------------------------------------------------------------

    def test_branch_b_stops_only_verified_new_ids_then_starts_the_rescue_once(self):
        key = self.partial_up()
        self.assertIsNone(self.docker.find(MANAGED))  # the up removed the original
        done = self.attempt().rescue()
        self.assertEqual(done["branch"], "B")
        stops = [run for run in self.docker.runs if run[:2] == ["docker", "stop"]]
        self.assertEqual(stops[-1], [*ret.STOP, "a" * 64, "e" * 64])
        self.assertEqual(self.docker.runs[-1], ["docker", "start", RESCUE])
        self.assertEqual(self.starts(RESCUE), 1)
        self.assertEqual(self.docker.find(RESCUE)["status"], "running")
        self.assertEqual(self.docker.find(CANDIDATE)["status"], "exited")
        timeouts = [(m[0][:2], m[1]) for m in self.mutations]
        self.assertEqual(
            timeouts,
            [
                (["docker", "stop"], ret.STOP_TIMEOUT),
                (["docker", "start"], ret.START_TIMEOUT),
            ],
        )
        self.assertTrue(all(m[3] for m in self.mutations))  # the lock held for both
        directory = self.attempt_dir(key)
        copy = (
            directory
            / "private"
            / f"rescue-result-{ret.RESCUE_RESULT_SHA256[:12]}.json"
        )
        self.assertEqual(stat.S_IMODE(copy.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(copy.parent.stat().st_mode), 0o700)
        self.assertEqual(copy.read_bytes(), self.receipts["rescue_result"].read_bytes())
        claim = json.loads((directory / "start-rescue.claim").read_text())
        gate = json.loads(Path(claim["gate"]["path"]).read_text())
        self.assertEqual(
            gate["gate"]["rescue_receipt"]["private_copy"]["sha256"],
            ret.RESCUE_RESULT_SHA256,
        )
        self.assertEqual(
            gate["gate"]["rescue"]["config_sha256"], ret.RESCUE_CONFIG_SHA256
        )
        self.assertEqual([r["id"] for r in gate["gate"]["new"]], ["a" * 64, "e" * 64])
        self.assertEqual(done["identity"]["config_sha256"], ret.RESCUE_CONFIG_SHA256)
        with self.assertRaisesRegex(
            RuntimeError, "HOLD: start-rescue.claim is consumed"
        ):
            self.attempt().rescue()
        with self.assertRaisesRegex(
            RuntimeError, "rescue branch already claimed stop-new"
        ):
            self.attempt().start_managed()
        self.assertEqual(self.starts(RESCUE), 1)

    def test_branch_b_refuses_an_unverified_new_id_and_stops_nothing(self):
        self.partial_up()
        brain = self.docker.containers[BRAIN]

        def working_dir():
            brain["labels"]["com.docker.compose.project.working_dir"] = "/elsewhere"

        def config_files():
            brain["labels"]["com.docker.compose.project.config_files"] = "compose.yaml"

        def image():
            brain["image_id"] = "sha256:" + "1" * 64

        def service():
            brain["labels"]["com.docker.compose.service"] = "worker"

        def created_before_the_stop():
            brain["created_at"] = "2026-11-07T20:00:00Z"

        def restarting():
            brain["status"] = "restarting"

        def short_id():
            brain["id"] = "e" * 12

        for change, message in (
            (working_dir, "working dir"),
            (config_files, "config files"),
            (image, "image"),
            (service, "service"),
            (created_before_the_stop, "created after the stop"),
            (restarting, "settled state"),
            (short_id, "full ID"),
        ):
            with self.subTest(change.__name__):
                saved = base.copy.deepcopy(brain)
                change()
                with self.assertRaisesRegex(
                    RuntimeError, f"unverified container .*{message}.*HOLD"
                ):
                    self.attempt().rescue()
                brain.clear()
                brain.update(saved)
        self.assertFalse(any(run[:2] == ["docker", "stop"] for run in self.mutations))
        self.assertEqual(self.starts(RESCUE), 0)

    def test_branch_b_refusals_before_the_rescue_start(self):
        key = self.partial_up()
        game = lambda: self.docker.containers[GAME]
        rescue = lambda: self.docker.find(RESCUE)

        def writer():
            self.docker.writers = 1

        def no_writer():
            self.docker.writers = 0

        def config():
            rescue()["env"] = [*rescue()["env"], "EXTRA=1"]

        def config_back():
            rescue()["env"] = rescue()["env"][:-1]

        cases = (
            (
                "new game restart",
                self.setting(game, restart="unless-stopped"),
                "not all stopped with restart=no",
            ),
            ("writer", (writer, no_writer), "other connection"),
            (
                "rescue config",
                (config, config_back),
                "differs from the manifest \\(config_sha256\\)",
            ),
            (
                "rescue restart",
                self.setting(rescue, restart="always"),
                "differs from the manifest \\(restart, config_sha256\\)",
            ),
            (
                "rescue image",
                self.setting(rescue, image_id="sha256:" + "2" * 64),
                "image_id",
            ),
        )
        for name, (change, undo), message in cases:
            with self.subTest(name):
                change()
                try:
                    with self.assertRaisesRegex(RuntimeError, message):
                        self.attempt().rescue()
                finally:
                    undo()
                self.assertFalse(
                    (self.attempt_dir(key) / "start-rescue.claim").exists()
                )
        self.assertEqual(self.starts(RESCUE), 0)
        stops = [m for m in self.mutations if m[0][:2] == ["docker", "stop"]]
        self.assertEqual(
            len(stops), 1
        )  # the verified stop ran once, before the first refusal
        self.attempt().rescue()  # a certain stop (exit 0) is not replayed; the start runs once
        stops = [m for m in self.mutations if m[0][:2] == ["docker", "stop"]]
        self.assertEqual(len(stops), 1)
        self.assertEqual(self.starts(RESCUE), 1)

    def test_branch_b_needs_an_up_attempt_and_a_wrong_rescue_config_refuses(self):
        self.stopped_attempt()
        with self.assertRaisesRegex(
            RuntimeError, "no up of this attempt was attempted"
        ):
            self.attempt().rescue()
        self.assertEqual(self.mutations, [])

    def test_branch_b_stop_failure_holds_and_never_starts_the_rescue(self):
        key = self.partial_up()
        self.docker.stop_exit = 0
        original = self.docker.run

        def failing(argv):
            original(argv)
            return (
                (1, "", "stop failed")
                if argv[:2] == ["docker", "stop"]
                else (0, "", "")
            )

        self.docker.run = failing
        with self.assertRaisesRegex(RuntimeError, "HOLD: stop-new exited 1"):
            self.attempt().rescue()
        with self.assertRaisesRegex(
            RuntimeError, "HOLD: stop-new.claim is consumed \\(exit 1"
        ):
            self.attempt().rescue()
        self.assertEqual(self.starts(RESCUE), 0)
        self.assertTrue((self.attempt_dir(key) / "stop-new.result").is_file())

    # -- exclusion, claims, uncertainty --------------------------------------------------------

    def test_a_busy_attempt_lock_is_hold_and_writes_nothing(self):
        key = self.stopped_attempt()
        directory = self.attempt_dir(key)
        for part in (self.legacy / "attempts", directory):
            part.mkdir(mode=0o700, exist_ok=True)
        descriptor = os.open(directory / ret.LOCK, os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)  # what the adapter holds during the up
        try:
            for branch in ("start_managed", "rescue"):
                with (
                    self.subTest(branch),
                    self.assertRaisesRegex(
                        RuntimeError, "HOLD: the attempt lock is held"
                    ),
                ):
                    getattr(self.attempt(), branch)()
        finally:
            os.close(descriptor)
        self.assertEqual(sorted(p.name for p in directory.iterdir()), [ret.LOCK])
        self.assertEqual(self.mutations, [])
        self.attempt().start_managed()  # the lock free again: the return runs
        self.assertEqual(self.starts(MANAGED), 1)

    def test_a_consumed_claim_refuses(self):
        key = self.stopped_attempt()
        directory = self.attempt_dir(key)
        directory.mkdir(parents=True, mode=0o700)
        (self.legacy / "attempts").chmod(0o700)
        (directory / "start-managed.claim").write_text('{"step": "start-managed"}\n')
        with self.assertRaisesRegex(
            RuntimeError, "claimed without a result: interrupted or uncertain"
        ):
            self.attempt().start_managed()
        self.assertEqual(self.mutations, [])

    def test_a_crash_after_the_claim_is_hold_with_no_replay(self):
        key = self.stopped_attempt()
        claim = self.attempt_dir(key) / "start-managed.claim"
        seen = []

        def mutate_then_crash(argv, timeout, keep):
            seen.append(claim.is_file())
            self.docker.run(argv)
            raise KeyboardInterrupt("power loss after the mutation")

        with (
            patch.object(ret, "run_mutation", side_effect=mutate_then_crash),
            self.assertRaisesRegex(
                RuntimeError, "HOLD: the outcome of start-managed is uncertain"
            ),
        ):
            self.attempt().start_managed()
        self.assertEqual(seen, [True])  # durable before the command
        self.assertFalse(claim.with_suffix(".result").exists())
        with self.assertRaisesRegex(
            RuntimeError, "without a result: interrupted or uncertain"
        ):
            self.attempt().start_managed()
        self.assertEqual(self.starts(MANAGED), 1)

    def test_a_mutation_timeout_is_uncertain_hold(self):
        key = self.stopped_attempt()
        with (
            patch.object(
                ret,
                "run_mutation",
                side_effect=subprocess.TimeoutExpired(
                    ["docker", "start"], ret.START_TIMEOUT
                ),
            ),
            self.assertRaisesRegex(RuntimeError, "uncertain \\(TimeoutExpired\\)"),
        ):
            self.attempt().start_managed()
        self.assertTrue((self.attempt_dir(key) / "start-managed.claim").is_file())
        self.assertFalse((self.attempt_dir(key) / "start-managed.result").exists())

    def test_a_probe_timeout_is_hold_and_never_read_as_absent(self):
        self.stopped_attempt()

        def hung(*args, env=None):
            if (
                args[:3] == ("docker", "inspect", MANAGED)
                and args[-1] == handoff.CONTAINER
            ):
                raise ret.ProbeTimeout(
                    "docker inspect timed out after 10 s; HOLD, no retry"
                )
            return self.command(*args, env=env)

        import preflight

        preflight.command.side_effect = hung
        with self.assertRaises(ret.ProbeTimeout):
            self.attempt().start_managed()
        self.assertEqual(self.mutations, [])

    def test_bound_tooling_gives_every_read_a_timeout(self):
        seen = []

        class Tooling:
            HERE = Path("/nonexistent")

        def run(args, **kwargs):
            seen.append(kwargs["timeout"])
            if args[1] == "slow":
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])
            return subprocess.CompletedProcess(args, 0, stdout="ok\n")

        tooling = Tooling()
        ret.bound_tooling(tooling, run=run)
        self.assertEqual(tooling.command("docker", "inspect"), "ok\n")
        with self.assertRaisesRegex(ret.ProbeTimeout, "timed out after 10 s; HOLD"):
            tooling.command("docker", "slow")
        self.assertEqual(seen, [ret.PROBE_TIMEOUT, ret.PROBE_TIMEOUT])
        self.assertFalse(issubclass(ret.ProbeTimeout, RuntimeError))
        self.assertLessEqual(ret.PROBE_TIMEOUT, 10)
        self.assertLessEqual(handoff.DB_PROBE_TIMEOUT, 10)

    def test_bindings_refuse_another_attempt_notice_manifest_or_stop(self):
        key = self.stopped_attempt()
        with self.assertRaisesRegex(RuntimeError, "stop claim .* absent or unreadable"):
            self.attempt("d" * 64).start_managed()
        with self.assertRaisesRegex(RuntimeError, "quiescent-pre-stop sha256"):
            self.attempt("not-a-sha")
        with self.assertRaisesRegex(RuntimeError, "window notice"):
            self.attempt(notice_sha="0" * 64).start_managed()
        with (
            patch.object(ret, "MANIFEST_SHA256", "0" * 64),
            self.assertRaisesRegex(RuntimeError, "manifest is not bc4fb5af"),
        ):
            self.attempt().start_managed()
        with (
            patch.object(ret, "RESCUE_CONFIG_SHA256", "0" * 64),
            self.assertRaisesRegex(RuntimeError, "rescue config"),
        ):
            self.attempt().start_managed()
        result = self.project / handoff.CLAIMS / f"{key}.quiescent-stop-game.result"
        body = json.loads(result.read_text())
        result.write_text(json.dumps({**body, "exit_code": 1}) + "\n")
        with self.assertRaisesRegex(
            RuntimeError, "not this attempt's quiescent stop with exit 0"
        ):
            self.attempt().start_managed()
        self.assertFalse(
            self.attempt_dir(key).exists()
        )  # nothing written before the bindings
        self.assertFalse(self.attempt_dir("d" * 64).exists())
        self.assertEqual(self.mutations, [])

    def test_the_adapter_copy_is_checked_before_any_of_its_code_runs(self):
        planted = self.root / "planted" / "stage2_handoff.py"
        planted.parent.mkdir()
        planted.write_text("raise SystemExit('the planted adapter ran')\n")
        with self.assertRaisesRegex(RuntimeError, "not --adapter-sha256"):
            ret.load_adapter(planted, sha(base.ADAPTER))
        saved = sys.modules["stage2_handoff"]
        try:
            module = ret.load_adapter(Path(handoff.__file__), sha(base.ADAPTER))
            self.assertIsNot(module, handoff)
            self.assertEqual(module.MANIFEST_SHA256, handoff.MANIFEST_SHA256)
        finally:
            sys.modules["stage2_handoff"] = saved

    def test_constants_are_the_reviewed_identities(self):
        self.assertEqual(
            ret.DERIVED_FROM,
            "52bac981b99d232e3336cb96722e1443bb01939540a05154292d8a98e535d04b",
        )
        self.assertEqual(ret.RESCUE, handoff.RESCUE_ID)
        game = next(c for c in self.baseline["containers"] if c["name"] == GAME)
        self.assertEqual(ret.MANAGED, game["id"])
        self.assertEqual(ret.MANAGED_IMAGE, base.gate.baseline_game_image())
        manifest = json.loads(base.MANIFEST.read_text())
        self.assertEqual(
            sha(base.MANIFEST.read_bytes()),
            "bc4fb5af6c1ff5ff76e08ac15125b463222bcbc27dc98b7b35a75f7f4f4202f0",
        )
        self.assertEqual(
            manifest["rescue_container_config"]["adapter_config_sha256"],
            "626ceb4905042d9410effb4a76da5b9c97432ab831cdccd4766ed6608482f4d2",
        )
        self.assertEqual(
            manifest["receipts"]["rescue_result"],
            "9f68b39c897aa2c274439d0e75d87cdaf8909f404729db5117a487ee0e143d9a",
        )
        self.assertEqual(
            manifest["containers"]["qa-old-rescue-20261107"]["image_id"],
            "sha256:78327d1a07a743683b0dc8f83c62edc4b4571098aa2b83e51e8bc6fdb0dfff72",
        )
        self.assertEqual(ret.CLAIM_ROOT, "runtime/evidence/qa-return-claims")


for _name in [*vars(base.HandoffTests), *vars(base.QuiescentTests)]:
    if _name.startswith("test_") and _name not in vars(ReturnAttemptTests):
        setattr(ReturnAttemptTests, _name, None)  # only the tests above run here
