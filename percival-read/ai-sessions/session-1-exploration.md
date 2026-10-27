# Session 1 — explore the inherited pipeline

Tool: Cursor (Composer). Fresh session. Task-only.

---

**User:** I inherited percival-read. Start from BRIEF.md / RULES.md / README. Run the pipeline and tests. Tell me where the code disagrees with RULES.md — don't fix yet.

**Assistant:** Ran `python run.py`, unittest (11 ok), eval 97.9% (A10 differs — usage minimum).

Likely rule disagreements I can see without editing:

1. `rules.live_status` lines 57–60: if `start <= as_of` and no activation row → `"live"`. Rule 11 says start date is not evidence.
2. `figures._top3_share`: publishes a complete % while `live` is already a `range`. Rule 16 wants unavailable or a bounded range when the total is incomplete.
3. No calculation records (rule sheet “calculation record” section). OUTPUT allows adding fields.
4. Loader is strict (`float(cell)`, fixed column names) — fine for room/, risky for hidden rooms.

Room A currently marks L018 (Pinecrest) live via the start-date fallback; management also has 48k. Under rule 11 it should be unknown.

**User:** Yeah L018 is the smoking gun. Hand-check L006 and the Calder amendment too and summarise what room A should look like under a strict reading.

**Assistant:**

- L004 superseded by L005; only L005 counts. L004 has go-live; L005 does not. Call needed: does the amendment inherit evidence?
- L006: 5 sites, 2 live on/before 2026-06-30, site 3 after as-of → `unknown`, do not prorate. L007 live 20k. A04 range 20k–140k matches current code.
- L018: no go-live row → `unknown` under rule 11 (today: live).
- L020 usage_minimum: recurring, 1500×12=18k, has go-live → live. Explains A10 vs reference (60k vs 78k).
- Top-3 52.63% is share-of-known; should not be a point fact while live is a range.

**User:** Stop here. Next session we fix live_status and top3. Don't touch the loader yet.
