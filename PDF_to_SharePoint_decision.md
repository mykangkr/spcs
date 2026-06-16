# Decision Doc — Pipeline for Uploading Generated PDFs to SharePoint

**Status:** Draft for team decision · **Owner:** _TBD_ · **Date:** 2026-06-16

## Context

The app (React + FastAPI on SPCS, Snowflake backend) will generate PDF reports
and deliver them to a SharePoint document library. Snowflake already has ADLS
access via storage integration. We need to choose the **delivery pipeline**
before building.

## Reality check

ADLS / Azure Blob ≠ SharePoint. Staging a file in blob storage does **not** put
it in a SharePoint library — *something* must still make the SharePoint hop via
the Microsoft Graph API. The patterns below differ in **who makes that hop,
where the Graph credentials live, and whether there's a buffer in front of it.**

## Options

| | A — Direct from SPCS | B — Blob/ADLS intermediary | C — In-Snowflake stage | D — Openflow |
|---|---|---|---|---|
| **Path** | App → Graph → SharePoint | App → Blob → mover → SharePoint | App → Snowflake → `COPY INTO` ADLS → mover → SharePoint | App → Snowflake/stage → Openflow (NiFi) → SharePoint |
| **Auth** | Direct Azure AD client creds (app-only, `Sites.Selected`) | mover holds Graph creds | mover holds Graph creds | Openflow connector holds creds |
| **SPCS egress** | Yes (External Access Integration) | Yes (to Blob endpoint) | **None** | **None** |
| **Creds live in** | Snowflake / container | Azure / M365 | Azure / M365 | Snowflake (Openflow) |
| **Immediacy** | Immediate | Eventual | Eventual | Eventual (flow-paced) |
| **Failure isolation** | Coupled to SharePoint uptime | Decoupled, retries | Decoupled | Decoupled, NiFi retry/backpressure |
| **Custom code** | Graph uploader | the mover | unload SQL + mover | mostly config |
| **Moving parts** | Fewest, all ours | +1 Azure component | +1 unload + 1 mover | +1 managed runtime |
| **Durable archive** | No (unless added) | Yes (blob) | Yes (ADLS + SF lineage) | Yes |
| **Best when** | Small app, instant delivery | Already run Azure-side code | Want egress-free staging + archive | Already adopting Openflow / broader content pipeline |

## Decisive questions

1. **Immediacy** — must the PDF appear in SharePoint instantly?
   *Yes → A · Eventual OK → B/C/D*
2. **Egress & secrets** — can SPCS make outbound calls and hold Graph secrets?
   *Egress OK → A · Avoid container egress → C/D · Keep creds in Azure → B/C*
3. **Org footprint** — what do we already run?
   *Only SPCS → A · An Azure mover → B/C · Openflow adopted/planned → D*
4. **Scope** — one-off feature, or first of many content/SharePoint flows?
   *One-off → A or C · Many / RAG → D*

## Recommendation

- **Default → A.** Direct Graph push with app-only Azure AD client credentials
  (`Sites.Selected`, certificate over secret) behind an External Access
  Integration. Fewest owners, simplest setup; right for a small internal app
  needing instant delivery.
- **If egress/secret governance is a hard blocker → C.** Exploits Snowflake's
  existing ADLS access so the container never calls out, and gives a durable
  archive for free. Accept eventual delivery + a dependency on the Azure mover.
- **Openflow (D) only if** we're already adopting it or SharePoint delivery is
  one of several integration flows — **and** only after confirming the
  *outbound* (Snowflake → SharePoint) direction is supported in our
  region/edition. Its SharePoint connector is oriented toward *ingestion*
  (SharePoint → Snowflake); outbound via generic NiFi processors is feasible
  but less-trodden. Don't stand up a managed runtime to upload one PDF.

**One-line steer:** start with **A** for speed unless egress/secret governance
blocks it (then **C**); reserve **D** for when SharePoint integration is a
program, not a feature.

## Open items to confirm with Azure/M365 team

- [ ] Outbound SharePoint support + maturity in Openflow (if D is in play).
- [ ] Which mover they already run (Power Automate / Logic App / Function) — tips B vs. C.
- [ ] Whether Graph secrets may live in Snowflake or must stay in Azure.
- [ ] Approval path/effort for an SPCS External Access Integration (if A).
- [ ] `COPY INTO` unload to the ADLS external stage works as expected (if C).

## Decision

> _Record the chosen pattern, who decided, and the rationale here once agreed._

- **Chosen pattern:** _____
- **Decided by / date:** _____
- **Rationale:** _____
