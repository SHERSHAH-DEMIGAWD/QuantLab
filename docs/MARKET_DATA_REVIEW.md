# Phase 9 market-data decision

Reviewed 2026-11-03 (Asia/Calcutta). **Selected: Path B, validated offline
workflow. Provider integration is unavailable/deferred, not implemented.**
This records Session 09's access decision. Session 11 subsequently verified
two public historical samples through the offline path; see the dated addendum.

## Alpha Vantage evaluation

| Concern | Official evidence and access limit |
| --- | --- |
| Daily fields/history | `TIME_SERIES_DAILY` documents raw dated OHLCV; compact gives the latest 100 observations, full history (25+ years) requires premium. No start/end parameters are listed; a future adapter would need explicit interval validation. |
| Adjustments | `TIME_SERIES_DAILY_ADJUSTED` is premium and includes raw OHLCV, adjusted close and events. Adjusted close must never replace only the close in raw OHLC. |
| Splits | `SPLITS` documents historical events and JSON/CSV. Account entitlement, complete interval coverage and usable empty-response semantics were not verified. Missing/failed evidence cannot become `none_reported`. |
| Authentication/format | An API key is required; daily outputs support JSON/CSV. |

Source: [official endpoint documentation](https://www.alphavantage.co/documentation/).
The split endpoint is not labeled premium on the reviewed page; this review
does **not** infer that it is paid-only or verify free access.

The [support FAQ](https://www.alphavantage.co/support/) states 25 free requests
per day and a separate allowance for verified educational/open-source projects.
QuantLab has not obtained that verification. Exact account throttling,
authentication/error envelopes and timeout behavior have not been exercised;
no live-response/error compatibility claim is made.

The [terms, sections 2-5](https://www.alphavantage.co/terms_of_service/) describe
personal noncommercial access, with broader/commercial uses requiring agreement,
and retained provider rights. This is not evidence of permission to redistribute
market observations in the repository or publish a shared data service. No
account was registered, subscription purchased or provider data redistributed.

## Why Path B

Presence-only checks found neither `ALPHAVANTAGE_API_KEY` nor
`ALPHA_VANTAGE_API_KEY` in the process environment; no secret value was read or
printed. No configured account, entitlement or licensed historical input was
available. A demo URL or mocked adapter would not satisfy the required real
permitted import or split-evidence verification. Per Session 09 authorization,
choose the fully working offline path rather than leave a partial integration.

Alpaca was not pursued: no clearly more feasible permitted live-import path was
established, and adding another provider would not resolve the missing verified
access/evidence. No market-data endpoint was called. Only public documentation,
support and terms were reviewed. No real historical dataset was acquired.

## Preserved boundary

D04 still requires consistent unadjusted OHLC, raw volume, `none_reported`
splits and explicit supporting evidence. Local-file coverage additionally needs
the existing acknowledgment; it does not certify completeness. Import validity
and simulation eligibility remain separate backend decisions. No adapter,
credentials UI, new endpoint, financial change or provider framework was added.

Working path: [offline guide](OFFLINE_DATA_GUIDE.md). Reconsidering a provider
requires explicit future authorization, permitted credentials/terms and a real
bounded import with adequate split evidence. Session 10 subsequently authorized
final engineering validation; it added no provider integration.

## Post-release addendum - Session 11, 2026-11-03

The new explicit task authorized real-history validation. No personal Alpha
Vantage/Alpaca environment credentials were available in the checked names.
Alpha Vantage's published `demo` access nevertheless returned genuine raw daily
samples for IBM and MSFT: 100 bars each, 2026-06-11..2026-11-02. These were used
only for private individual noncommercial testing under the reviewed terms;
observations, issuer-page archives and SQLite files remain ignored. No
redistribution permission or general account entitlement was inferred.

IBM's split query succeeded with no listed event inside the imported interval.
MSFT's split response contained only an access message, so that response's
split assessment remains unknown. Microsoft's published issuer history provided
separate evidence supporting the selected interval. No adapter was added.

Alpaca was reviewed as the longer-history alternative: its documented bars
support raw adjustments, explicit feeds and pagination, but authentication is
required. Without local credentials no Alpaca data request, entitlement test or
feed-coverage assertion was made. Exact sources, receipts/hashes, tests and
limits now have their primary home in [REAL_MARKET_VALIDATION.md](REAL_MARKET_VALIDATION.md).
