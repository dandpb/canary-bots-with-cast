# R2 failed qualification: financial reconciliation

Canonical cutoff: 2026-11-06T18:21:10.457077+00:00; closed wrapper cutoff: 2026-11-06T18:16:10.203764+00:00.

One read-only SQLite/WAL transaction covers global balance, selected prior7 plus new3, claim COUNT and quick_check. Claim data is not read. The claim remains consumed and is not a billable request. Unknown reservations remain intact; financial_final is false. Gemini was not evaluated in R2 and no scored games were created; older v1 Gemini costs remain counted. No retry, release or provider call was performed by this audit.
