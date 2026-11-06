# Infrastructure follow-up for interrupted attempts A

The original A bundle in `../m5-final-interrupted-attempts` remains unchanged and **not accepted**. These later receipt projections add context for the infrastructure interruption; they do not replace its recording, missing canonical exports or original cleanup result.

At 13:27:15 UTC, read-only probes recorded five native status rows per worker and `getwd: no such file or directory`. The process-directory `pwd -P` failed, while the expected path resolved. At 13:35:28 UTC, the coordinator's original receipt recorded a graceful SIGTERM request for the two validated QA workers, classified `infrastructure_cwd_lost`.

External fallback receipts document cleanup **after** the original worker exits, with canonical `saved-character.json` still absent. Their external character readings remain labelled external: native XP 101220, fake XP 101612. They are not canonical exports and do not turn the interrupted attempts into 30-minute rounds. Both report zero remaining containers/networks after fallback cleanup.

This evidence concerns a host working-directory failure and its recorded interruption response. It does not establish a model-quality failure or a Redis cause. Earlier artifacts retain what was known at their publication time; these supplemental receipts do not rewrite them.

`checksums.json` covers the allowlist projections. Each receipt retains the SHA256 of its private original, without process/container IDs, argv, environment, credentials or private host paths. This consolidation read existing files only, without signalling workers or accessing runtime/DBs.
