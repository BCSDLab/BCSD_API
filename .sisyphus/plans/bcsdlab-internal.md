# BCSDLab INTERNAL - Google Workspace Automation System

## TL;DR

> **Quick Summary**: Build a club management automation system using n8n to orchestrate Google Workspace (Sheets as database, Forms for input, Docs for reports). FastAPI is optional glue for authorization checks (SpiceDB) when needed.
> 
> **Deliverables**: 
> - n8n + Google Workspace integration (Forms → Sheets → automated workflows)
> - Fee management automation (payment tracking, reminders, notifications)
> - Member lifecycle automation (registration, onboarding, status transitions)
> - Optional: FastAPI + SpiceDB for hierarchical authorization
> - Docker Compose environment for local dev + production
> 
> **Estimated Effort**: Large (45-70 hours for MVP, includes data migration)
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Google API Setup → n8n Foundation → Data Migration → Core Workflows → Authorization Layer
> **Timeline**: No hard deadline - quality over speed, incremental delivery encouraged

---

## Context

### Original Request
Build a FastAPI backend for BCSDLab club management system to automate:
- Fee payment tracking and notifications
- Member lifecycle management (Beginner → Regular → Mentor)
- Administrative task automation (ledger, reports, notifications)
- Hierarchical group permissions (organization → track → team)

### Architecture Clarification Journey

**Initial Understanding (Incorrect)**: Multi-database system with FastAPI as main backend, Google Sheets as one of five databases with complex sync.

**Final Architecture (Correct)**: **Google Workspace IS the database.** n8n orchestrates everything by directly calling Google APIs. FastAPI is optional, minimal, only for authorization checks when needed.

### Final Architecture

**Core Principle**: Google Workspace is the platform, n8n is the automation engine.

```
Google Forms (input) → n8n (orchestration) → Google Sheets (database) → n8n (logic) → Slack/Email (output)
                                                                     ↓
                                              Optional: FastAPI → SpiceDB (authorization only)
```

**Components**:
- **n8n**: PRIMARY - orchestrates all workflows, directly manipulates Google APIs
- **Google Sheets**: Source of truth for member data, fees, groups (EXISTING DATA will be migrated)
- **Google Forms**: Input interface for members
- **Google Docs**: Report generation
- **Slack**: BCSDLab workspace already exists with admin access
- **FastAPI**: OPTIONAL - only for SpiceDB authorization checks, secret management
- **SpiceDB**: OPTIONAL - hierarchical permissions (if fine-grained auth needed)
- **PostgreSQL/Redis/MongoDB**: OPTIONAL - use only if Sheets truly can't handle it

**Key Insight**: No sync operations. n8n writes directly to Sheets. That's the database.

**User Confirmed**:
- ✅ Existing Google Sheets data needs migration to new structured schema
- ✅ BCSDLab Slack workspace exists with admin access (ready for bot creation)
- ✅ No hard deadline - can proceed at comfortable pace (2-3 weeks estimated)

---

## Work Objectives

### Core Objective
Create a Google Workspace-based automation system using n8n to eliminate manual administrative tasks for BCSDLab club operations, with optional authorization layer (FastAPI + SpiceDB) for sensitive operations.

### Concrete Deliverables
- **Google Workspace Structure**: Structured Sheets (members, fees, groups, events), Forms templates, Docs templates
- **n8n Workflows**: Fee tracking, payment reminders, member onboarding, status transitions, scheduled reports
- **Docker Compose Environment**: n8n, optional FastAPI, optional SpiceDB, with proper networking and secrets
- **Documentation**: Workflow usage guide, Google Workspace setup guide, emergency procedures
- **Optional Authorization System**: FastAPI endpoints + SpiceDB schema for hierarchical permissions

### Definition of Done
- [ ] n8n connects to Google Workspace APIs successfully
- [ ] Fee payment form submission → auto-recorded in Sheets → reminder sent if unpaid
- [ ] New member registration form → auto-added to Sheets + Slack → onboarding triggered
- [ ] Scheduled workflow runs (e.g., weekly fee reminder) execute successfully
- [ ] Docker Compose brings up entire stack with one command
- [ ] If authorization enabled: SpiceDB checks work via FastAPI endpoint

### Must Have
- n8n Docker container running and accessible
- Google Workspace API credentials configured (service account or OAuth)
- At least ONE working end-to-end workflow (fee payment or member registration)
- Google Sheets with proper structure (tabs for members, fees, groups)
- Basic error handling in n8n workflows (what if Sheets API fails?)

### Must NOT Have (Guardrails)
- ❌ **Complex database sync logic** - Sheets IS the database, no sync needed
- ❌ **FastAPI as default gateway** - only use when authorization or complex logic required
- ❌ **Over-abstraction** - keep n8n workflows simple and readable
- ❌ **Premature optimization** - start with working workflows, optimize later
- ❌ **All workflows at once** - build incrementally, one workflow at a time
- ❌ **PostgreSQL/MongoDB unless proven necessary** - default to Sheets first

---

## Business Logic Specifications

### Fee Lifecycle Specification (CRYSTAL CLEAR - Momus Required)

**CRITICAL: Read this section completely before implementing Tasks 6-7. No assumptions allowed.**

#### 1. Data Model Choice: PAYMENT-LOGGING (Not Invoice Model)

**What this means**:
- The `fees` table is a **historical log of payments received**, NOT a list of invoices owed
- A row in `fees` exists ONLY when money has been received
- There are NO pre-generated "invoice" rows waiting to be marked as paid

**Why this matters**:
- When someone submits the fee payment form → new row added to `fees`
- When someone hasn't paid → NO row exists in `fees` for that member/semester
- Reminders are sent by ABSENCE of payment record, not by presence of unpaid invoice

#### 2. Due Date Semantics: CALCULATED AT REMINDER TIME

**Q: Where does `fees.due_date` come from?**  
**A: It doesn't exist in the `fees` table (payment log).**

**Confusion Point Resolved**:
- Task 3 schema shows `fees` with columns: `id`, `member_id`, `amount`, `paid_date`, `payment_method`, `notes`, `last_updated`
- **NO `due_date` column in fees table** (it was a mistake in the example - executor should ignore it)
- "Due date" is a PERIOD-LEVEL concept, not a payment-level concept

**How Reminders Compute "Overdue/Within 7 Days"**:
- Hard-coded rule: "Monthly fees due first Monday of each month"
- Task 7 runs every Monday at 9am (cron schedule)
- Reminder logic: "It's Monday → fees are due → check who hasn't paid this month → send reminder"
- No database column needed - it's implicit in the schedule

**Pseudo-SQL for Reminder Check**:
```sql
-- Run every Monday at 9am
SELECT members.email, members.name
FROM members
WHERE members.payment_status = 'Unpaid'
  AND members.status IN ('Regular', 'Beginner')  -- Don't remind Mentors (they're Exempt)
  AND members.email NOT IN (
      SELECT DISTINCT fees.member_id  
      FROM fees 
      WHERE fees.semester = '2024-1'  -- Current semester, hardcoded in workflow for MVP
  )
```

#### 3. Payment Status State Machine: EXACT TRANSITIONS

**`members.payment_status` Values**:
- `Unpaid` - Member owes fees for current period
- `Paid` - Member has paid for current period  
- `Exempt` - Member doesn't owe fees (Mentors, Alumni)
- `null` (empty) - Treated same as `Unpaid` (backward compatibility)

**State Transition Table**:

| From | To | Trigger | Workflow | Condition |
|------|----|---------| ---------|-----------|
| `Unpaid` | `Paid` | Fee payment form submitted | Task 6 | Payment received and logged |
| `Paid` | `Unpaid` | Start of new semester | Task 7 (manual reset) | New semester begins (2024-1 → 2024-2) |
| `Unpaid` or `Paid` | `Exempt` | Member promoted to Mentor | Task 9 | Status transition to Mentor |
| `Exempt` | `Unpaid` | Mentor demoted to Regular | Task 9 | Status transition from Mentor |

**Authoritative Workflows**:
- Task 6 is authoritative for `Unpaid` → `Paid` (when payment submitted)
- Task 7 does NOT automatically reset status (admin manually resets at semester start using Task 9 bulk update)
- Task 9 is authoritative for `Exempt` status (based on member role)

**Example Scenario**:
1. Semester starts: Admin runs bulk update via Task 9 to set all Regular members to `Unpaid`
2. Member submits payment → Task 6 sets `payment_status = 'Paid'`
3. Every Monday: Task 7 checks for `Unpaid` members → sends reminders
4. Member promoted to Mentor → Task 9 sets `payment_status = 'Exempt'` → no more reminders

#### 4. Fees Table Schema (FINAL, NO CHANGES)

**Columns** (exactly these, no more):
- `id` (text): `F-{timestamp}-{rand3}` (e.g., `F-20240128150000-X7K`)
- `member_id` (text): Foreign key to `members.id` (e.g., `M-20240115120000-A2B`)
- `amount` (number): Amount paid in KRW (e.g., 10000)
- `paid_date` (date): YYYY-MM-DD when payment was made (from form submission)
- `payment_method` (text): "Bank Transfer" | "Cash" | "Mobile Payment"
- `notes` (text): Optional notes from payment form
- `semester` (text): "2024-1" | "2024-2" | "2025-1" etc. (hardcoded in form/workflow for MVP)
- `last_updated` (datetime): Timestamp when row created

**NO `due_date` column** - this was confusion from initial spec. Ignore it.

#### 5. MVP Simplifications (Locked Decisions)

- **Single fee amount**: 10,000 KRW per member per month (configurable constant in Task 6 workflow)
- **Semester tracking**: Simple string "YYYY-S" where S=1 (Spring) or S=2 (Fall)
- **Payment period**: Monthly (can aggregate to semester total later)
- **Reminder frequency**: Weekly on Mondays (cron: `0 9 * * 1` = 9am every Monday KST)
- **Status reset**: Manual admin action at semester start (not automatic)

**Decision Locked**: Payment-logging model with implicit due dates. Cannot change without plan revision.

---

### Technical Decisions (Addresses Momus Issues #2-3)

**Trigger Mechanism (Momus Issue #2)**:

- **MVP Default**: Google Sheets trigger (polling mode, 1-2 min delay)
- **NOT USING**: Apps Script webhooks (adds complexity, requires script deployment)
- **Rationale**: Simpler setup, acceptable delay for club use case
- Tasks 6, 8 use: n8n "Google Sheets Trigger" node watching response tabs
- Task 9 uses: n8n "Webhook" node (manual admin trigger via form Apps Script)
  - Exception: Admin forms need instant trigger (status changes are time-sensitive)
  - Apps Script in admin form: `UrlFetchApp.fetch(n8n_webhook_url, {method: 'POST', payload: formData})`

**Notification Strategy (Momus Issue #2)**:

- **MVP Primary**: Email (SMTP via n8n Email Send node)
- **Post-MVP**: Slack DM (requires Slack app setup, adds in Task 7/8 if time permits)
- **Decision**: Task 7 MUST have email, Slack is optional enhancement
- **Rationale**: Email works immediately, Slack requires bot token setup

**Data Integrity Rules (Momus Issue #3)**:

1. **Uniqueness Constraints**:
   - `members.email`: MUST be unique (primary lookup key)
   - `members.id`: MUST be unique (primary key)
   - `fees.id`: MUST be unique (primary key)
   - `groups.id`: MUST be unique (primary key)

2. **ID Format Specification**:
   - `members.id`: `M-{YYYYMMDDHHmmss}-{random3}` (e.g., `M-20240128143022-A7K`)
   - `fees.id`: `F-{YYYYMMDDHHmmss}-{random3}` (e.g., `F-20240128143500-B2X`)
   - `groups.id`: `G-{YYYYMMDDHHmmss}-{random3}` (e.g., `G-20240128140000-C9Z`)
   - Random suffix prevents collisions if multiple records created in same second
   - Generated by n8n expression: `{{$now.toFormat('yyyyMMddHHmmss')}}-{{$randomString(3).toUpperCase()}}`

3. **Primary Key and Foreign Key Strategy (EXPLICIT)**:
   
   **Primary Keys**:
   - `members.id` is the primary key (NOT email)
   - Email is a unique field used for lookups, but ID is the permanent identifier
   
   **Foreign Keys**:
   - `fees.member_id` references `members.id` (stores the M-xxx-xxx ID string)
   - Lookups always done by email (user-friendly), but FKs store ID (stable)
   
   **Task 6 Workflow Example (Fee Payment Form Submitted)**:
   ```
   Step 1: Form submitted with member_email="alice@bcsdlab.com", amount=10000
   Step 2: n8n Lookup node → Search members tab WHERE email="alice@bcsdlab.com"
   Step 3a: IF FOUND → Extract member.id (e.g., "M-20240115120000-A2B")
   Step 3b: IF NOT FOUND → ERROR (go to error branch)
   Step 4: Generate fee.id using expression: `F-{{$now.toFormat('yyyyMMddHHmmss')}}-{{$randomString(3).toUpperCase()}}`
   Step 5: Append to fees tab: {
     id: "F-20240128153000-XYZ",
     member_id: "M-20240115120000-A2B",  ← Foreign key stores ID, not email
     amount: 10000,
     paid_date: "2024-01-28",
     payment_method: "Bank Transfer",
     semester: "2024-1"
   }
   Step 6: Update members tab: SET payment_status="Paid" WHERE email="alice@bcsdlab.com"
   ```
   
   **Error Handling (Email Not Found)**:
   ```
   IF lookup returns no rows:
     - Log to workflow_logs: "ERROR: Member not found for email alice@bcsdlab.com"
     - Send email to admin: "Payment submitted by unknown member"
     - DO NOT create fees row (payment rejected)
     - STOP workflow
   ```

4. **Join Strategy (n8n Implementation)**:
   - All n8n "Google Sheets Lookup" operations use `email` column as search key
   - After successful lookup, extract `id` field from result
   - Use extracted ID when writing foreign key columns
   - Never store email in foreign key columns (store ID instead)

---

### Migration Specification (EXECUTABLE - Momus Required)

**CRITICAL: Task 5.5 executor must fill in actual sheet URLs, but here are concrete templates.**

#### Source Sheets Inventory (Expected Structure)

**Executor Action Required**: Before migration, identify and document existing sheets here:

| Sheet Name | Owner | URL | Purpose | Expected Columns |
|------------|-------|-----|---------|------------------|
| "BCSDLab Fees 2023-2024" | VP Email | `https://docs.google.com/spreadsheets/d/...` | Historical fee payments | Name, Email, Amount, Date, Semester |
| "BCSDLab Member List" | President Email | `https://docs.google.com/spreadsheets/d/...` | Current member directory | Name, Email, Track, Join Date, Status |
| "Track Assignments" (if exists) | Track Leader | `https://docs.google.com/spreadsheets/d/...` | Track/team structure | Member Email, Track, Team |

**If sheets don't exist or are unusable**: Document in migration log and start fresh (no migration needed).

#### Column Mapping Table (CONCRETE EXAMPLE)

**Assumption**: Old sheets have inconsistent column names. Map them to new schema:

| Source | Old Column | Target | New Column | Transformation Rule | n8n Expression |
|--------|------------|--------|------------|---------------------|----------------|
| Fees Sheet | "회원 이름" or "Name" | members | name | Direct copy, trim whitespace | `{{$json["회원 이름"].trim()}}` |
| Fees Sheet | "이메일" or "Email" | members | email | Lowercase, validate format | `{{$json["이메일"].toLowerCase()}}` |
| Fees Sheet | "납부액" or "Amount" | fees | amount | Parse as number, default 10000 | `{{parseInt($json["납부액"]) \|\| 10000}}` |
| Fees Sheet | "납부일" or "Date" | fees | paid_date | Parse Korean date (YYYY.MM.DD or YYYY-MM-DD) | `{{DateTime.fromFormat($json["납부일"], "yyyy.MM.dd").toISODate()}}` |
| Member Sheet | "가입일" or "Join Date" | members | join_date | Parse date, default to "2024-01-01" if missing | `{{$json["가입일"] ? DateTime.fromISO($json["가입일"]).toISODate() : "2024-01-01"}}` |
| Member Sheet | "트랙" or "Track" | members | track | Map Korean to English: "프론트"→"Frontend", "백엔드"→"Backend" | Use n8n Switch node |

**Executor fills missing mappings during Task 5.5 based on actual sheet structure.**

#### Deduplication Logic (SQL-LIKE SPECIFICATION)

**Rule**: Keep row with most recent data when duplicate emails found.

**Pseudo-SQL**:
```sql
-- For members table
SELECT *
FROM (
  SELECT *, 
         ROW_NUMBER() OVER (PARTITION BY email ORDER BY last_updated DESC, join_date DESC) as rn
  FROM migrated_members_raw
)
WHERE rn = 1
```

**n8n Implementation**:
1. Aggregate node: Group by `email`
2. Sort within group: By `last_updated` DESC (or `join_date` DESC if no `last_updated`)
3. Take first item in each group
4. Output: Deduplicated members

**If >10% duplicates** (e.g., >20 out of 200 members):
- Log warning to `migration_errors` tab
- Create separate `duplicates_review` tab with all duplicate rows
- Admin manually reviews and deletes unwanted rows

#### Validation Rules (EXECUTABLE CHECKS)

**Email Validation**:
```javascript
// n8n Code node
const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
if (!emailRegex.test(item.email)) {
  return { valid: false, error: `Invalid email: ${item.email}` };
}
return { valid: true };
```

**Required Fields Check**:
- members: MUST have `email`, `name`
- fees: MUST have `member_id` (or email to lookup ID), `amount`, `paid_date`
- If any required field missing → log to `migration_errors` tab with row data

**Data Type Validation**:
- `amount` must be numeric: `!isNaN(parseFloat(amount))`
- `paid_date` must parse as date: `DateTime.fromISO(paid_date).isValid`
- `email` must match regex (above)

#### Active Member Definition (FOR FILTERING)

**Rule**: Migrate only members active within last 2 years.

**SQL-like Filter**:
```sql
SELECT * FROM members
WHERE join_date >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR)
   OR last_updated >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR)
   OR status IN ('Regular', 'Beginner')  -- Always include current members
```

**n8n Implementation**:
```javascript
// Code node filter
const twoYearsAgo = DateTime.now().minus({ years: 2 });
const joinDate = DateTime.fromISO(item.join_date);
const lastUpdated = item.last_updated ? DateTime.fromISO(item.last_updated) : null;

if (item.status === 'Regular' || item.status === 'Beginner') {
  return true;  // Always include current members
}
if (joinDate >= twoYearsAgo) {
  return true;  // Joined recently
}
if (lastUpdated && lastUpdated >= twoYearsAgo) {
  return true;  // Updated recently
}
return false;  // Filter out (Alumni from >2 years ago)
```

#### Data Volume Estimate and Batch Processing

**Expected Volumes**:
- Members: 50-200 rows
- Fees: 200-1000 rows
- If >1000 rows total: Use n8n "Split In Batches" node (batch size 100)

**Batch Processing Logic**:
```
Split In Batches node:
  - Batch size: 100 rows
  - For each batch:
    1. Transform data (map columns)
    2. Validate (check required fields)
    3. Deduplicate (if needed)
    4. Append to new Sheets (batch write)
  - After all batches: Verify row count matches
```

#### Migration Checklist (EXECUTOR MUST COMPLETE)

- [ ] Step 1: Create backup copies of all source sheets (rename with "BACKUP-YYYY-MM-DD" prefix)
- [ ] Step 2: Fill in actual source sheet URLs in inventory table above
- [ ] Step 3: Inspect actual column names and fill in mapping table
- [ ] Step 4: Run test migration on first 10 rows, verify transformations work
- [ ] Step 5: Run full migration, log all validation errors
- [ ] Step 6: Manually review `migration_errors` tab and `duplicates_review` tab
- [ ] Step 7: Fix critical errors (missing emails, invalid data), re-run if needed
- [ ] Step 8: Verify final row counts: source vs target (should match within 5%)
- [ ] Step 9: Document in `docs/migration-log.md`: what was migrated, what was skipped, known issues
- [ ] Step 10: Archive original sheets (move to "ARCHIVED" folder, don't delete)

**Decision Locked**: Executor fills placeholders during Task 5.5. Core migration logic is specified above.

---

### Package Naming Correction (Addresses Momus Issue #5)

**Decision**: Change `kut_internal` to `bcsdlab_internal`

**Rationale**:
- This project is for BCSDLab (not Korea University of Technology)
- Package should reflect actual organization name
- Task 11 updated to use `src/bcsdlab_internal/` for FastAPI package

**Note**: If user later clarifies BCSDLab IS at KUT, can revert. For now, using explicit org name.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (greenfield project)
- **User wants tests**: Manual verification + integration tests
- **Framework**: Manual QA for n8n workflows, pytest for FastAPI (if built)

### Manual Verification Strategy

**For n8n Workflows (PRIMARY)**:
Each workflow is verified by:
1. **Test Execution**: Manually trigger workflow in n8n UI
2. **Input Validation**: Use test Google Form submissions
3. **Output Verification**: Check Google Sheets for correct data writes
4. **Side Effect Verification**: Check Slack messages, emails sent
5. **Error Handling**: Trigger failure scenarios (invalid input, API down)

**For FastAPI Endpoints (OPTIONAL, if built)**:
- pytest with test database
- Integration tests with SpiceDB testcontainer
- Manual verification via curl/httpie

### Verification Tools by Deliverable

| Deliverable Type | Verification Tool | Procedure |
|------------------|------------------|-----------|
| **n8n Workflow** | n8n UI + Google Sheets | Execute workflow → Check Sheets updated → Verify notifications sent |
| **Google Sheets Structure** | Manual inspection | Open Sheets → Verify tabs exist → Check headers match schema |
| **Docker Compose** | docker compose CLI | `docker compose up` → All services healthy → n8n UI accessible |
| **FastAPI Endpoint** | curl / pytest | `curl POST /check-auth` → 200 OK → Response body correct |
| **SpiceDB Schema** | SpiceDB CLI | `zed validate` → Schema valid → Test permission checks work |

---

## Execution Strategy

### Parallel Execution Waves

> Tasks grouped into waves to maximize throughput. Each wave completes before the next begins.

```
Wave 1 (Foundation - Start Immediately):
├── Task 1: Docker Compose base setup (n8n + dependencies)
├── Task 2: Google Workspace API setup (service account, credentials)
└── Task 3: Google Sheets structure design (schema documentation)

Wave 2 (After Wave 1 - n8n Development + Data Prep):
├── Task 4: n8n Google Sheets integration (connect + test read/write)
├── Task 5: Create Google Forms templates (fee payment, member registration)
└── Task 5.5: Migrate existing Sheets data to new schema (NEW - CRITICAL)

Wave 3 (After Wave 2 - Core Workflows):
├── Task 6: First workflow - Fee payment recording (Form → Sheets, uses migrated data)
├── Task 7: Fee reminder workflow (scheduled, reads Sheets, sends notifications)
├── Task 8: Member registration workflow (Form → Sheets + Slack + onboarding)
└── Task 9: Member status transition workflow (Beginner → Regular → Mentor)

Wave 4 (After Wave 3 - Optional Authorization):
├── Task 10: [DECISION POINT] Do we need SpiceDB? If YES → continue, if NO → skip to Task 13
├── Task 11: FastAPI project setup + SpiceDB integration
├── Task 12: Authorization workflow in n8n (call FastAPI before sensitive operations)
└── Task 13: Documentation + deployment guide

Critical Path: Task 1 → Task 4 → Task 5.5 → Task 6 → Task 7 → Task 13
Parallel Speedup: ~30% faster than sequential (Waves 2-3 have parallelism)
Note: Task 5.5 (data migration) is CRITICAL - all workflows depend on clean migrated data
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 4 | 2, 3 |
| 2 | None | 4 | 1, 3 |
| 3 | None | 5, 5.5 | 1, 2 |
| 4 | 1, 2 | 5.5, 6, 7, 8 | 5 |
| 5 | 3 | 8 | 4 |
| 5.5 | 3, 4 | 6, 7, 8, 9 | None (CRITICAL - must complete before workflows) |
| 6 | 5.5 | None | 7, 8, 9 |
| 7 | 5.5 | None | 6, 8, 9 |
| 8 | 5, 5.5 | None | 6, 7, 9 |
| 9 | 5.5 | None | 6, 7, 8 |
| 10 | None | 11, 12 | None (decision point) |
| 11 | 10 (if YES) | 12 | None |
| 12 | 11 | None | None |
| 13 | All others | None | None (final) |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 2, 3 | unspecified-low (setup tasks) |
| 2 | 4, 5, 6 | unspecified-high (n8n workflow development) |
| 3 | 7, 8, 9 | unspecified-high (complex workflows) |
| 4 | 11, 12, 13 | quick (FastAPI) + writing (docs) |

---

## TODOs

### Wave 1: Foundation (Start Immediately)

---

- [ ] **1. Docker Compose Infrastructure Setup**

  **What to do**:
  - Create `docker-compose.yml` with services: n8n, PostgreSQL (for n8n's metadata), Redis (optional, for n8n queue mode)
  - Configure n8n with environment variables (timezone, webhook URL, encryption key)
  - Set up volumes for n8n data persistence (`~/.n8n` directory)
  - Create `.env.example` with required variables template
  - Add health checks for all services
  - Configure network bridge for inter-service communication

  **Must NOT do**:
  - Don't add FastAPI, SpiceDB, MongoDB to compose file yet (we'll decide later if needed)
  - Don't overcomplicate with Kubernetes/production orchestration (Docker Compose is fine for MVP)
  - Don't hardcode secrets in compose file (use .env)

  **Tools Used**: Docker Compose only (no n8n workflows, no FastAPI)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Infrastructure setup task, straightforward Docker Compose configuration
  - **Skills**: None needed (basic Docker knowledge)
  - **Skills Evaluated but Omitted**:
    - N/A - standard Docker task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Task 4 (n8n must be running to test integrations)
  - **Blocked By**: None (can start immediately)

  **References**:

  **Docker Compose Patterns**:
  - Official n8n Docker docs: `https://docs.n8n.io/hosting/installation/docker/` - Docker Compose example, environment variables
  - n8n Docker docs: `https://docs.n8n.io/hosting/installation/docker/` - Official Docker setup (working link verified)

  **Configuration Examples**:
  - Environment variables needed: `N8N_BASIC_AUTH_ACTIVE`, `N8N_HOST`, `WEBHOOK_URL`, `GENERIC_TIMEZONE`
  - Volume mounts: `~/.n8n:/home/node/.n8n` for workflow persistence

  **Why Each Reference Matters**:
  - n8n docs provide official recommended setup (must follow for stability)
  - GitHub examples show production patterns (health checks, restart policies)

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [ ] Command: `docker compose up -d`
  - [ ] Expected: All services start successfully (n8n, PostgreSQL, Redis if included)
  - [ ] Command: `docker compose ps`
  - [ ] Expected output contains: `n8n` with status `Up (healthy)` or `running`
  - [ ] Command: `curl http://localhost:5678`
  - [ ] Expected: n8n login page HTML (status 200)
  - [ ] Browser: Navigate to `http://localhost:5678`
  - [ ] Expected: n8n UI loads, can create account/login

  **Evidence Required**:
  - [ ] Screenshot of n8n UI loaded in browser
  - [ ] Terminal output of `docker compose ps` showing all services running
  - [ ] `.env.example` file exists with template variables

  **Commit**: YES
  - Message: `feat(infra): add Docker Compose setup for n8n`
  - Files: `docker-compose.yml`, `.env.example`, `.gitignore` (add `.env`)
  - Pre-commit: `docker compose config` (validates YAML syntax)

  **Estimated Effort**: Small (<2h)

---

- [ ] **2. Google Workspace API Setup & Credentials**

  **What to do**:
  - Create Google Cloud Project for BCSDLab Internal
  - Enable Google Sheets API, Google Drive API, Google Forms API
  - Create Service Account with appropriate permissions
  - Generate service account JSON key file
  - Share target Google Sheets with service account email (editor permission)
  - Document the setup process (step-by-step guide for future reference)
  - Store credentials securely (add to `.env`, add `credentials.json` to `.gitignore`)

  **Must NOT do**:
  - Don't commit credentials to git (add to .gitignore immediately)
  - Don't use personal Google account for service account (use BCSDLab organization if possible)
  - Don't over-scope permissions (only Sheets, Drive, Forms needed initially)

  **Tools Used**: Google Cloud Console (manual setup, no code yet)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Configuration task following documented steps
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**:
    - N/A - cloud console configuration

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Task 4 (credentials needed for n8n to connect)
  - **Blocked By**: None (can start immediately)

  **References**:

  **API Setup Documentation**:
  - Google Sheets API quickstart: `https://developers.google.com/sheets/api/quickstart/python` - Service account setup steps
  - Google Cloud Console: `https://console.cloud.google.com/` - Where to create project and enable APIs

  **Service Account Best Practices**:
  - Naming convention: `bcsdlab-internal@[project-id].iam.gserviceaccount.com`
  - Permissions: "Editor" role on specific Sheets (not owner, for safety)

  **n8n Google Sheets Credentials**:
  - n8n docs: `https://docs.n8n.io/integrations/builtin/credentials/google/` - How to add service account credentials to n8n

  **Why Each Reference Matters**:
  - Quickstart guide provides step-by-step CLI commands
  - n8n credentials docs show exactly how to paste service account JSON into n8n UI

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [ ] Google Cloud Console shows enabled APIs: Sheets, Drive, Forms
  - [ ] Service account exists with name `bcsdlab-internal-sa` (or similar)
  - [ ] Service account JSON key downloaded and saved to `credentials/google-service-account.json` (gitignored)
  - [ ] Command: `cat credentials/google-service-account.json | jq .type`
  - [ ] Expected output: `"service_account"`
  - [ ] Test Google Sheet exists and is shared with service account email
  - [ ] Sheet URL documented in setup guide

  **Evidence Required**:
  - [ ] Screenshot of Google Cloud Console showing enabled APIs
  - [ ] Service account email saved to `.env` file (as `GOOGLE_SERVICE_ACCOUNT_EMAIL`)
  - [ ] Setup guide document created (Markdown) with step-by-step instructions

  **Commit**: YES
  - Message: `docs(setup): add Google Workspace API setup guide`
  - Files: `docs/google-api-setup.md`, `.env.example` (add GOOGLE_* variables), `.gitignore` (add credentials/)
  - Pre-commit: Manual review (ensure no credentials committed)

  **Estimated Effort**: Small (<2h)

---

- [ ] **3. Google Sheets Database Schema Design**

  **What to do**:
  - Create a new Google Sheets workbook: "BCSDLab Internal Database"
  - Design sheet tabs (worksheets) for each data entity:
    - `members` tab: columns (id, name, email, status, track, team, join_date, payment_status, last_updated)
    - `fees` tab: columns (id, member_id, amount, due_date, paid_date, payment_method, notes, last_updated)
    - `groups` tab: columns (id, name, type, parent_id, size, leader_email, last_updated)
    - `events` tab: columns (id, title, date, type, organizer, attendees, notes)
    - `workflow_logs` tab: columns (timestamp, workflow_name, status, input_data, output_data, error_message)
  - Add header rows with clear column names
  - Document schema in `docs/sheets-schema.md` (data dictionary with column descriptions)
  - Add data validation rules where appropriate (e.g., status must be "Beginner", "Regular", or "Mentor")
  - Share sheet with service account (editor permission)

  **Must NOT do**:
  - Don't create overly complex relational structure (Sheets isn't a relational DB)
  - Don't add too many tabs initially (start with core entities, expand later)
  - Don't use formulas extensively (logic should be in n8n, not Sheets)

  **Tools Used**: Google Sheets UI (manual setup), documentation in Markdown

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Data modeling task, straightforward schema design
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**:
    - N/A - spreadsheet design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Tasks 5, 6 (forms and workflows need schema to reference)
  - **Blocked By**: None (can start immediately)

  **References**:

  **Database Design in Sheets**:
  - Reference from user context: `https://dbdiagram.io/d/인터널-DB-개편-2-67d0673675d75cc844b12de8` - Hierarchical group structure
  - Reference from user context: `https://dbdocs.io/psb106305/BCSDLab_Internal_Restructuring?view=table_structure` - Database schema documentation

  **Materialized Path Pattern**:
  - For hierarchical groups: Use `parent_id` column to reference parent group
  - Example: Organization (id=1, parent_id=NULL) → Track (id=2, parent_id=1) → Team (id=3, parent_id=2)

  **Sheets Best Practices**:
  - Always include `last_updated` timestamp column (for conflict detection if needed later)
  - Use `id` column with unique values (can be auto-generated by n8n workflow)
  - Data validation: Google Sheets UI → Data → Data validation (restrict dropdown values)

  **Why Each Reference Matters**:
  - dbdiagram.io shows entity relationships to model
  - dbdocs.io provides column-level documentation to replicate
  - Materialized path pattern enables hierarchical queries in flat Sheets structure

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [ ] Google Sheets workbook created with name "BCSDLab Internal Database"
  - [ ] Workbook contains tabs: `members`, `fees`, `groups`, `events`, `workflow_logs`
  - [ ] Each tab has header row with column names matching schema
  - [ ] `members` tab includes columns: id, name, email, status, track, team, join_date, payment_status, last_updated
  - [ ] Data validation rule on `members.status`: dropdown with ["Beginner", "Regular", "Mentor", "Alumni"]
  - [ ] Sheet shared with service account email (from Task 2) with "Editor" permission
  - [ ] Documentation file `docs/sheets-schema.md` exists with data dictionary

  **Evidence Required**:
  - [ ] Screenshot of Google Sheets tabs list
  - [ ] Screenshot of `members` tab with header row visible
  - [ ] Copy of Sheets URL saved to `.env` as `GOOGLE_SHEETS_DATABASE_URL`

  **Commit**: YES
  - Message: `docs(schema): add Google Sheets database schema design`
  - Files: `docs/sheets-schema.md`, `.env.example` (add GOOGLE_SHEETS_DATABASE_URL)
  - Pre-commit: Manual review of schema documentation

  **Estimated Effort**: Small (<2h)

---

### Wave 2: n8n Development Foundation (After Wave 1)

---

- [ ] **4. n8n Google Sheets Integration & Connection Test**

  **What to do**:
  - Access n8n UI (from Task 1 Docker setup)
  - Add Google Sheets credentials to n8n:
    - Credentials → Add Credential → Google Sheets API (Service Account)
    - Paste service account JSON content
    - Test connection
  - Create test workflow: "Test Sheets Connection"
    - Trigger: Manual execution
    - Node 1: Google Sheets (Read operation) - read `members` tab
    - Node 2: Google Sheets (Append operation) - add test row to `workflow_logs` tab
    - Node 3: Set node - display data
  - Execute test workflow and verify:
    - Can read existing data from Sheets
    - Can write new rows to Sheets
    - Data appears correctly in Google Sheets UI
  - Document connection setup in `docs/n8n-setup.md`

  **Must NOT do**:
  - Don't create complex workflows yet (just test connection)
  - Don't add error handling logic yet (basic success path only)
  - Don't integrate with other services yet (Sheets only for now)

  **Tools Used**: n8n UI (visual workflow editor), Google Sheets

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: n8n workflow development requires understanding of node configuration and data flow
  - **Skills**: None specific (n8n is low-code but needs logical thinking)
  - **Skills Evaluated but Omitted**:
    - N/A - n8n is self-contained

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5)
  - **Parallel Group**: Wave 2 (with Task 5, partially with 6)
  - **Blocks**: Tasks 6, 7, 8, 9 (all workflows need working Sheets connection)
  - **Blocked By**: Tasks 1, 2 (needs n8n running + credentials)

  **References**:

  **n8n Google Sheets Node Documentation**:
  - n8n Sheets node: `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/` - All operations (read, append, update, lookup)
  - Authentication setup: `https://docs.n8n.io/integrations/builtin/credentials/google/` - Service account credential configuration

  **n8n Workflow Basics**:
  - n8n workflow fundamentals: `https://docs.n8n.io/workflows/` - How workflows execute, how to pass data between nodes
  - Testing workflows: `https://docs.n8n.io/workflows/test-your-workflows/` - Manual execution, debugging

  **Google Sheets API Operations**:
  - Read range: Specify sheet name (e.g., `members`) or range (e.g., `members!A1:Z100`)
  - Append row: Automatically adds to next empty row
  - Batch operations: Important for performance (mentioned in research findings)

  **Why Each Reference Matters**:
  - n8n Sheets node docs show exact parameter names and options
  - Workflow fundamentals explain node execution order (critical for data flow)
  - API operations reference ensures correct usage (avoid rate limits)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Using n8n UI:**
  - [ ] Navigate to n8n UI at `http://localhost:5678`
  - [ ] Credentials page shows "Google Sheets API (Service Account)" with status "Connected" (green checkmark)
  - [ ] Workflow "Test Sheets Connection" exists
  - [ ] Click "Execute Workflow" button in workflow editor
  - [ ] Expected: Workflow executes successfully (all nodes show green checkmarks)
  - [ ] Click on "Google Sheets" read node → "Table" view shows data from `members` tab
  - [ ] Open Google Sheets in browser
  - [ ] Expected: `workflow_logs` tab has new row with test data (timestamp, "Test Sheets Connection", "success")

  **Using Command Line (alternative verification)**:
  - [ ] Command: `docker compose logs n8n | grep "Successfully executed"`
  - [ ] Expected output contains: workflow execution success message

  **Evidence Required**:
  - [ ] Screenshot of n8n workflow editor showing successful execution (all green nodes)
  - [ ] Screenshot of Google Sheets `workflow_logs` tab with test row
  - [ ] n8n workflow exported as JSON to `workflows/test-sheets-connection.json`

  **Commit**: YES
  - Message: `feat(n8n): add Google Sheets integration test workflow`
  - Files: `workflows/test-sheets-connection.json` (exported workflow), `docs/n8n-setup.md` (setup guide)
  - Pre-commit: Manual verification that workflow JSON is valid

  **Estimated Effort**: Medium (2-4h)

---

- [ ] **5. Create Google Forms Templates for Data Entry**

  **What to do**:
  - Create Google Form: "Fee Payment Submission"
    - Fields: Member Email, Amount Paid, Payment Date, Payment Method (dropdown), Receipt Screenshot (file upload), Notes (optional)
    - Set response destination: "BCSDLab Internal Database" Google Sheets → NEW tab `fee_payment_responses`
    - Enable email collection
  - Create Google Form: "New Member Registration"
    - Fields: Full Name, Email, Phone Number, Track Selection (dropdown: Frontend, Backend, Android, iOS, Design), Preferred Team (text), Introduction (long text)
    - Response destination: Same Sheets → NEW tab `member_registration_responses`
  - Configure form settings:
    - Require sign-in (to prevent spam)
    - Collect email addresses
    - Response receipts: Always
  - Document form URLs in `docs/forms-guide.md`
  - Test each form: submit test responses, verify they appear in Sheets

  **Must NOT do**:
  - Don't add complex form logic (conditional sections, etc.) yet (keep forms simple)
  - Don't integrate with n8n yet (that's next task)
  - Don't create too many forms upfront (start with 2 essential ones)

  **Tools Used**: Google Forms UI (manual setup), Google Sheets (auto-destination)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Form creation is straightforward configuration
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**:
    - N/A - Google Forms is user-friendly

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 4)
  - **Parallel Group**: Wave 2 (with Task 4)
  - **Blocks**: Task 5.5 (migration needs forms for testing), Task 8 (registration workflow needs form)
  - **Blocked By**: Task 3 (needs schema to know what fields to include)

  **References**:

  **Google Forms Best Practices**:
  - Google Forms documentation: `https://support.google.com/docs/answer/6281888` - Creating forms, response settings
  - Forms → Sheets integration: `https://support.google.com/docs/answer/2917686` - How to connect form responses to Sheets

  **Form Design for Automation**:
  - Field validation: Use Google Forms validation (email format, number range)
  - Dropdown options: Must match Sheets data validation (e.g., track names)
  - File upload: Requires Google Drive permissions (service account must have access)

  **Why Each Reference Matters**:
  - Official docs show response destination setup (critical for Sheets integration)
  - Field validation reduces bad data (less error handling needed in n8n)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **For Fee Payment Form**:
  - [ ] Google Form exists with title "BCSDLab - Fee Payment Submission"
  - [ ] Form includes fields: Member Email (email validation), Amount Paid (number), Payment Date (date), Payment Method (dropdown), Receipt (file upload optional), Notes (text)
  - [ ] Form settings: "Collect email addresses" enabled, "Require sign-in" enabled
  - [ ] Submit test response through form
  - [ ] Open "BCSDLab Internal Database" Google Sheets
  - [ ] Expected: New tab `fee_payment_responses` exists with test submission data
  - [ ] Verify columns match form fields (Timestamp, Email, Member Email, Amount Paid, etc.)

  **For Member Registration Form**:
  - [ ] Google Form exists with title "BCSDLab - New Member Registration"
  - [ ] Form includes fields: Full Name, Email (email validation), Phone Number, Track Selection (dropdown with Frontend/Backend/Android/iOS/Design), Preferred Team, Introduction
  - [ ] Submit test response through form
  - [ ] Expected: New tab `member_registration_responses` exists in Sheets with test data

  **Evidence Required**:
  - [ ] Screenshot of both forms' edit view showing all fields
  - [ ] Screenshot of Sheets tabs list showing `fee_payment_responses` and `member_registration_responses`
  - [ ] Form URLs saved to `docs/forms-guide.md` with usage instructions

  **Commit**: YES
  - Message: `feat(forms): create fee payment and member registration forms`
  - Files: `docs/forms-guide.md` (with form URLs and field descriptions)
  - Pre-commit: Manual test of both forms

  **Estimated Effort**: Small (<2h)

---

- [ ] **5.5. Migrate Existing Google Sheets Data to New Schema** *(NEW - CRITICAL)*

  **What to do**:
  - Identify existing Google Sheets with BCSDLab data (fee records, member directory, etc.)
  - Create n8n workflow: "Data Migration - One Time"
  - Workflow logic:
    1. Manual trigger (run once)
    2. Node: Read existing fee records from old Sheets
    3. Node: Transform data to match new schema (map old columns → new columns)
    4. Node: Data validation (check for missing required fields, invalid formats)
    5. Node: Deduplication (check for duplicate entries by email or ID)
    6. Node: Append validated data to new `fees` tab
    7. Repeat for members, groups, and other data
    8. Node: Generate migration report (how many records migrated, errors found)
    9. Node: Log to `workflow_logs` (migration completed)
  - Manual fallback: If data volume is small or messy, manually copy-paste and clean
  - Document which old Sheets were migrated and keep them as backup (rename to "ARCHIVED - Old Data")
  - Verify data integrity after migration (spot-check sample records)

  **Must NOT do**:
  - Don't delete old Sheets immediately (keep as backup for 1-2 months)
  - Don't auto-merge dirty data (validate and flag errors for manual review)
  - Don't assume schema matches perfectly (map carefully, document transformations)
  - Don't migrate irrelevant historical data (only active members, recent fees)

  **Tools Used**: n8n workflow OR manual spreadsheet operations (depends on data complexity)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Data transformation requires careful mapping and validation logic
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - data migration task

  **Parallelization**:
  - **Can Run In Parallel**: NO (CRITICAL - all workflows depend on this)
  - **Parallel Group**: Sequential (must complete before any workflow runs)
  - **Blocks**: Tasks 6, 7, 8, 9 (all workflows need migrated data)
  - **Blocked By**: Tasks 3, 4 (needs new schema designed + n8n connected)

  **References**:

  **Data Migration Best Practices**:
  - Always backup original data before migration (make copy of old Sheets)
  - Validate data types: dates must be dates, numbers must be numbers
  - Handle missing data: decide on default values or skip records
  - Document transformation rules: old field X → new field Y

  **n8n Data Transformation**:
  - Set node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.set/` - Transform and map fields
  - Code node: `https://docs.n8n.io/code/` - Custom JavaScript for complex transformations
  - Split In Batches node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.splitinbatches/` - Process large datasets in chunks

  **Data Validation Patterns**:
  - Email validation: Regex check for valid email format
  - Date validation: Parse dates, handle different formats (YYYY-MM-DD vs MM/DD/YYYY)
  - Deduplication: Group by email or ID, keep most recent record

  **Why Each Reference Matters**:
  - Backup prevents data loss if migration has errors
  - Set node is primary tool for field mapping in n8n
  - Split In Batches prevents timeout on large datasets (>1000 rows)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Before Migration:**
  - [ ] Identify all existing Sheets with data (list URLs in `docs/migration-log.md`)
  - [ ] Create backup copies with names: "BACKUP - [Original Name] - [Date]"
  - [ ] Document old schema: What columns exist? What do they mean?

  **Run Migration:**
  - [ ] If using n8n workflow:
    - Workflow "Data Migration - One Time" exists
    - Execute workflow manually
    - Check execution log for errors
    - Migration report generated (e.g., "150 members migrated, 3 errors")
  - [ ] If using manual copy-paste:
    - Copy data from old Sheets to new tabs
    - Transform columns to match new schema
    - Validate data (no missing emails, dates formatted correctly)

  **After Migration:**
  - [ ] New Sheets `members` tab has data (count matches old data ± errors)
  - [ ] Spot-check 5-10 random records: data looks correct, no corruption
  - [ ] `fees` tab has fee records with proper foreign keys (member_id references members.id)
  - [ ] `groups` tab has organizational structure
  - [ ] Document in `docs/migration-log.md`:
    - What was migrated (tables, record counts)
    - What was skipped (irrelevant historical data)
    - Any known data quality issues
  - [ ] Old Sheets renamed: "ARCHIVED - [Original Name]"

  **Evidence Required**:
  - [ ] Screenshot of new Sheets with migrated data (show row count)
  - [ ] Migration log document (`docs/migration-log.md`) with details
  - [ ] If using n8n: Migration workflow exported to `workflows/data-migration-onetime.json`

  **Commit**: YES
  - Message: `feat(migration): migrate existing Sheets data to new schema`
  - Files: `docs/migration-log.md`, `workflows/data-migration-onetime.json` (if used)
  - Pre-commit: Verify data integrity (spot-check sample records)

  **Estimated Effort**: Medium-Large (3-8h, depends on data volume and quality)

---

- [ ] **6. First n8n Workflow - Fee Payment Recording**

  **What to do**:
  - Create n8n workflow: "Fee Payment Processing"
  - **Trigger (MVP LOCKED)**: Google Sheets trigger node (watches `fee_payment_responses` tab for new rows, polling interval 1-2 min)
  - **NOT USING**: Apps Script webhooks (adds complexity, deferred to post-MVP)
  - Workflow logic:
    1. Trigger: When new row added to `fee_payment_responses` (detected by polling)
    2. Node: Extract data (member_email, amount, paid_date, payment_method, notes)
    3. Node: Lookup member in `members` tab by email → get `members.id`
    4. Node: IF member found:
       a. Generate fee ID: `F-{timestamp}-{random3}` using expression
       b. Append to `fees` tab: (id=generated, member_id=looked up ID, amount, paid_date, payment_method, semester="2024-1", notes)
       c. Update `members` tab: SET payment_status="Paid", last_updated=NOW() WHERE email=member_email
       d. Log to `workflow_logs`: (timestamp, workflow_name="Fee Payment Processing", status="success", input_data=email+amount)
    5. Node: IF member NOT found:
       a. Log to `workflow_logs`: (timestamp, workflow_name="Fee Payment Processing", status="error", error_message="Member not found: {email}")
       b. Send email notification to admin (configured admin email address)
  - Test workflow with form submission from Task 5
  - Verify data flows correctly through all nodes
  - Export workflow JSON to `workflows/` directory

  **Must NOT do**:
  - Don't use webhooks (Sheets polling trigger is simpler and sufficient)
  - Don't add Slack notifications in this task (email only for MVP, Slack in Task 7/8 if time permits)
  - Don't overcomplicate error handling (basic logging + admin email is enough)

  **Tools Used**: n8n workflow (Sheets trigger + Sheets operations)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex workflow with multiple nodes, conditional logic, data transformations
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - n8n-specific task

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 8, 9 in Wave 3)
  - **Parallel Group**: Wave 3 (with Tasks 7, 8, 9)
  - **Blocks**: None (workflows are independent after this)
  - **Blocked By**: Task 5.5 (CRITICAL - needs migrated data in Sheets)

  **References**:

  **n8n Node Types Needed**:
  - Google Sheets Trigger: `https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.googlesheetstrigger/` - Watches for new rows
  - Google Sheets node operations: Lookup, Update, Append
  - IF node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/` - Conditional branching
  - Set node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.set/` - Transform data

  **Workflow Patterns**:
  - Error handling in n8n: `https://docs.n8n.io/workflows/error-handling/` - Try/catch pattern
  - Data transformation: `https://docs.n8n.io/code/builtin/data-transformation-functions/` - Expressions for data manipulation

  **Sheets Operations**:
  - Lookup operation: Search `members` tab where column "email" equals form submission email
  - Update operation: Update specific row in `members` or `fees` tab
  - Append operation: Add new row to `fees` tab

  **Why Each Reference Matters**:
  - Trigger node is critical (determines when workflow runs)
  - IF node enables conditional logic (member found vs not found)
  - Error handling docs show how to catch failures gracefully

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Using n8n UI + Google Forms + Sheets:**
  - [ ] Workflow "Fee Payment Processing" exists in n8n
  - [ ] Workflow is activated (toggle switch in UI is ON)
  - [ ] Submit test fee payment via Google Form (from Task 5)
    - Email: test-member@bcsdlab.com (must exist in `members` tab first - add manually)
    - Amount: 10000
    - Payment Date: Today's date
    - Method: Bank Transfer
  - [ ] Wait 1-2 minutes for trigger to fire (Sheets trigger has polling interval)
  - [ ] n8n workflow execution history shows successful run
  - [ ] Open Google Sheets:
    - `fee_payment_responses` tab has the form submission
    - `fees` tab has new row with member_id (looked up), amount 10000, paid_date matching submission
    - `members` tab shows test-member@bcsdlab.com with `payment_status` = "Paid", `last_updated` = recent timestamp
    - `workflow_logs` tab has entry with workflow_name="Fee Payment Processing", status="success"

  **Error Case Verification:**
  - [ ] Submit form with non-existent email (not in `members` tab)
  - [ ] Expected: `workflow_logs` shows error status with message "Member not found: [email]"

  **Evidence Required**:
  - [ ] Screenshot of n8n workflow diagram (all nodes visible)
  - [ ] Screenshot of successful execution in n8n (green checkmarks on all nodes)
  - [ ] Screenshot of Google Sheets `fees` tab with new test record
  - [ ] Workflow exported to `workflows/fee-payment-processing.json`

  **Commit**: YES
  - Message: `feat(workflow): add fee payment processing workflow`
  - Files: `workflows/fee-payment-processing.json`, `docs/workflow-guide.md` (add workflow documentation)
  - Pre-commit: Test workflow execution manually

  **Estimated Effort**: Medium (3-5h)

---

### Wave 3: Core Automation Workflows (After Wave 2)

---

- [ ] **7. Fee Reminder Workflow - Scheduled Automation**

  **What to do**:
  - Create n8n workflow: "Fee Payment Reminder"
  - Trigger: Schedule (Cron) - run every Monday at 9:00 AM KST
  - Workflow logic:
    1. Trigger: Cron schedule
    2. Node: Read `members` tab → filter rows where `payment_status` = "Unpaid" OR `payment_status` is empty
    3. Node: Read `fees` tab → join with members to get fee details (amount, due_date)
    4. Node: Filter members where `due_date` is past (overdue) or within 7 days (upcoming)
    5. Node: For each member → Send reminder via Slack DM or Email
    6. Node: Update `workflow_logs` with summary (X reminders sent)
  - Add Slack integration:
    - BCSDLab Slack workspace already exists (confirmed)
    - Create Slack app in workspace (if not already done)
    - Add Slack credentials to n8n (bot token with scopes: `chat:write`, `users:read`, `users:read.email`)
    - Use Slack node to send DM to member (lookup Slack user by email)
  - Alternative if Slack integration delayed: Use Email node (SMTP or SendGrid) temporarily
  - Test workflow: Manually execute, verify reminders sent

  **Must NOT do**:
  - Don't send to all members (filter for unpaid only)
  - Don't spam (run scheduled, not on every execution)
  - Don't overcomplicate message template (simple reminder text is fine)

  **Tools Used**: n8n workflow (Schedule trigger + Sheets read + Slack/Email)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Scheduled workflow with filtering, external API integration (Slack)
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - n8n + Slack integration

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 6, 8, 9)
  - **Parallel Group**: Wave 3 (with Tasks 6, 8, 9)
  - **Blocks**: None (standalone workflow)
  - **Blocked By**: Task 5.5 (needs migrated members and fees data)

  **References**:

  **n8n Scheduling**:
  - Cron node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.cron/` - Schedule syntax (every Monday 9am = `0 9 * * 1`)
  - Timezone configuration: Set `GENERIC_TIMEZONE=Asia/Seoul` in n8n environment

  **Slack Integration**:
  - n8n Slack node: `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.slack/` - Send message, lookup user by email
  - Slack API credentials: Create Slack app, add OAuth scopes (`chat:write`, `users:read`, `users:read.email`)

  **Email Alternative**:
  - n8n Email node (SMTP): `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.emailsend/`

  **Data Filtering in n8n**:
  - Filter node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.filter/` - Conditional filtering
  - Date comparisons: Use expressions like `{{DateTime.now().minus({days: 7})}}`

  **Why Each Reference Matters**:
  - Cron syntax must be correct (wrong schedule = wrong reminder timing)
  - Slack credentials setup is critical (missing scopes = API errors)
  - Filter node prevents sending reminders to paid members (avoids annoyance)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Setup Test Data:**
  - [ ] Manually add test members to `members` tab:
    - Member 1: email=unpaid@test.com, payment_status="Unpaid", Slack email match
    - Member 2: email=paid@test.com, payment_status="Paid"
  - [ ] Add fee records to `fees` tab:
    - Fee for Member 1: due_date = 7 days ago (overdue)
    - Fee for Member 2: due_date = today, paid_date = today

  **Execute Workflow:**
  - [ ] Workflow "Fee Payment Reminder" exists and is activated
  - [ ] Manually click "Execute Workflow" (don't wait for schedule)
  - [ ] n8n execution shows successful run
  - [ ] Check Slack DM to unpaid@test.com user
  - [ ] Expected: Message received with text like "Hi [Name], your fee payment of [Amount] was due on [Date]. Please pay soon."
  - [ ] Check Slack DM to paid@test.com user
  - [ ] Expected: NO message received (filtered out)
  - [ ] `workflow_logs` tab shows entry with "1 reminder sent"

  **Schedule Verification:**
  - [ ] Wait until next Monday 9:00 AM KST (or change cron to test sooner)
  - [ ] Expected: Workflow automatically executes at scheduled time (check n8n execution history)

  **Evidence Required**:
  - [ ] Screenshot of n8n workflow with Schedule trigger and all nodes
  - [ ] Screenshot of Slack DM showing reminder message
  - [ ] Workflow exported to `workflows/fee-payment-reminder.json`

  **Commit**: YES
  - Message: `feat(workflow): add scheduled fee payment reminder`
  - Files: `workflows/fee-payment-reminder.json`, `docs/workflow-guide.md` (update with reminder workflow)
  - Pre-commit: Manual test execution

  **Estimated Effort**: Medium (3-5h)

---

- [ ] **8. Member Registration & Onboarding Workflow**

  **What to do**:
  - Create n8n workflow: "New Member Onboarding"
  - Trigger: Google Sheets trigger on `member_registration_responses` tab (new row)
  - Workflow logic:
    1. Trigger: New form submission in `member_registration_responses`
    2. Node: Extract data (name, email, phone, track, team, introduction)
    3. Node: Generate member ID (timestamp-based or UUID)
    4. Node: Append to `members` tab (id, name, email, status="Beginner", track, team, join_date=today, payment_status="Unpaid")
    5. Node: Send welcome email to new member (with next steps guide)
    6. Node: Add member to Slack workspace (Slack invite API)
    7. Node: Create Google Drive folder for member (in "BCSDLab Members" shared drive)
    8. Node: Add member to appropriate Google Calendar (track-specific calendar invite)
    9. Node: Log to `workflow_logs` (member onboarded successfully)
  - Error handling: If Slack invite fails, log but continue (email sent as fallback)
  - Test with form submission from Task 5

  **Must NOT do**:
  - Don't create all onboarding steps at once (start with Sheets write + email, expand later)
  - Don't fail entire workflow if one step fails (use error handling to continue)
  - Don't add complex approval logic yet (auto-accept for MVP)

  **Tools Used**: n8n workflow (Sheets + Email + Slack + Google Drive + Google Calendar)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex multi-service integration workflow
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - integration-heavy task

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 6, 7, 9)
  - **Parallel Group**: Wave 3 (with Tasks 6, 7, 9)
  - **Blocks**: None (standalone workflow)
  - **Blocked By**: Task 5 (registration form), Task 5.5 (migrated data)

  **References**:

  **n8n Integrations Needed**:
  - Slack: Send invitation - `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.slack/` - Use "Invite User to Workspace" action
  - Google Drive: Create folder - `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googledrive/` - "Create Folder" operation
  - Google Calendar: Create event - `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecalendar/` - "Create Event" operation
  - Email: Send welcome message - Use Email node with template

  **Workflow Error Handling**:
  - Error trigger: `https://docs.n8n.io/workflows/error-handling/` - Catch errors and continue workflow
  - Retry logic: n8n node settings → Retry On Fail (3 attempts, 5 sec delay)

  **Data Transformation**:
  - Generate UUID: Use expression `{{$now.toISO()}}` or `{{$randomString(10)}}`
  - Format date: `{{DateTime.now().toISODate()}}` for join_date

  **Why Each Reference Matters**:
  - Slack invite requires admin token (must configure in credentials)
  - Google Drive folder creation needs shared drive ID (must set up first)
  - Error handling prevents workflow from stopping if Slack fails (email continues)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Submit Test Registration:**
  - [ ] Fill out "New Member Registration" form with test data:
    - Name: Test Newbie
    - Email: newbie@test.com
    - Track: Backend
    - Team: API Development
    - Introduction: "Hello, I'm excited to join!"
  - [ ] Submit form
  - [ ] Wait for n8n trigger (1-2 minutes)

  **Verify Each Step:**
  - [ ] Google Sheets `members` tab has new row:
    - name="Test Newbie", email="newbie@test.com", status="Beginner", track="Backend", join_date=today
  - [ ] Email received at newbie@test.com with subject "Welcome to BCSDLab!"
  - [ ] Slack workspace shows pending invitation for newbie@test.com (or auto-added if Slack settings allow)
  - [ ] Google Drive "BCSDLab Members" shared drive has new folder "Test Newbie"
  - [ ] Google Calendar (Backend track calendar) has new member added or invite sent
  - [ ] `workflow_logs` tab shows entry with status="success", output_data includes all completed steps

  **Error Case:**
  - [ ] Submit form with email that already exists in `members` tab
  - [ ] Expected: Workflow logs error "Duplicate member" but doesn't crash

  **Evidence Required**:
  - [ ] Screenshot of Google Sheets `members` tab with new member
  - [ ] Screenshot of welcome email in inbox
  - [ ] Screenshot of Google Drive folder created
  - [ ] Workflow exported to `workflows/member-onboarding.json`

  **Commit**: YES
  - Message: `feat(workflow): add member registration and onboarding automation`
  - Files: `workflows/member-onboarding.json`, `docs/workflow-guide.md` (update)
  - Pre-commit: Full end-to-end test

  **Estimated Effort**: Large (5-8h)

---

- [ ] **9. Member Status Transition Workflow (Beginner → Regular → Mentor)**

  **What to do**:
  - Create n8n workflow: "Member Status Transition"
  - Trigger: Webhook (to be called manually by admin or via form submission)
  - Workflow input: member_email, new_status, reason (optional)
  - Workflow logic:
    1. Trigger: Webhook receives transition request
    2. Node: Validate input (status must be "Beginner", "Regular", "Mentor", or "Alumni")
    3. Node: Lookup member in `members` tab by email
    4. Node: If member found → Update status, update last_updated timestamp
    5. Node: If new_status = "Regular" → Send congratulations message, update fee structure (Regular members pay different amount)
    6. Node: If new_status = "Mentor" → Mark payment_status as "Exempt" (Mentors don't pay)
    7. Node: Send notification to member (email + Slack DM) about status change
    8. Node: Update `groups` tab if needed (add to new group, remove from old group)
    9. Node: Log to `workflow_logs` (transition completed)
  - Create admin interface: Simple Google Form for status transitions
    - Fields: Member Email, New Status (dropdown), Reason (text)
    - Form submission → triggers this workflow
  - Test all transition paths (Beginner→Regular, Regular→Mentor, Regular→Alumni)

  **Must NOT do**:
  - Don't auto-transition based on time/metrics (manual admin trigger only for MVP)
  - Don't add complex approval workflows (admin decision is final)
  - Don't create UI (Google Form is sufficient)

  **Tools Used**: n8n workflow (Webhook + Sheets update + notifications)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: State machine logic with multiple transition paths
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - workflow automation task

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 6, 7, 8)
  - **Parallel Group**: Wave 3 (with Tasks 6, 7, 8)
  - **Blocks**: None (standalone workflow)
  - **Blocked By**: Task 5.5 (needs migrated members data)

  **References**:

  **n8n Webhook Trigger**:
  - Webhook node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/` - Receives HTTP requests
  - Webhook URL format: `http://localhost:5678/webhook/member-status-transition`

  **Workflow State Machine Pattern**:
  - Switch node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.switch/` - Route based on new_status value
  - Multiple branches: Beginner→Regular path, Regular→Mentor path, etc.

  **Sheets Update Operations**:
  - Update row: Find row by email, update status column
  - Conditional updates: IF new_status="Mentor" THEN payment_status="Exempt"

  **Notification Templates**:
  - Congratulations message for Regular: "Congrats on becoming a Regular member!"
  - Mentor notification: "Thank you for becoming a Mentor. You are exempt from fees."

  **Why Each Reference Matters**:
  - Webhook trigger enables admin to trigger transitions (via form or API)
  - Switch node allows different logic per status transition (clean branching)
  - Sheets update must be atomic (don't partially update if notification fails)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Setup:**
  - [ ] Create Google Form "Member Status Transition" (admin-only, share link with VPs)
    - Fields: Member Email, New Status (dropdown: Beginner/Regular/Mentor/Alumni), Reason
    - Form connected to n8n webhook (use Apps Script to POST to webhook URL)

  **Test Transition: Beginner → Regular**
  - [ ] Add test member to `members` tab: email=transition-test@test.com, status="Beginner"
  - [ ] Submit status transition form: Email=transition-test@test.com, New Status=Regular, Reason="Completed onboarding"
  - [ ] Verify in Google Sheets `members` tab:
    - status="Regular"
    - last_updated=recent timestamp
  - [ ] Verify email sent to transition-test@test.com with subject "Congratulations!"
  - [ ] Verify Slack DM sent (if Slack integrated)
  - [ ] `workflow_logs` shows successful transition

  **Test Transition: Regular → Mentor**
  - [ ] Update test member status to "Regular" manually
  - [ ] Submit form: New Status=Mentor
  - [ ] Verify `members` tab: status="Mentor", payment_status="Exempt"
  - [ ] Verify notification sent: "Thank you for becoming a Mentor"

  **Error Case:**
  - [ ] Submit form with non-existent email
  - [ ] Expected: workflow_logs shows error "Member not found"

  **Evidence Required**:
  - [ ] Screenshot of n8n workflow with Switch node showing all transition paths
  - [ ] Screenshot of Google Sheets showing status updated
  - [ ] Screenshot of notification email
  - [ ] Workflow exported to `workflows/member-status-transition.json`

  **Commit**: YES
  - Message: `feat(workflow): add member status transition workflow`
  - Files: `workflows/member-status-transition.json`, `docs/workflow-guide.md` (update), `docs/forms-guide.md` (add admin form)
  - Pre-commit: Test all transition paths

  **Estimated Effort**: Medium (4-6h)

---

### Wave 4: Optional Authorization Layer (After Wave 3)

---

- [ ] **10. [DECISION POINT] Authorization Requirements Analysis**

  **What to do**:
  - Review completed workflows (Tasks 6-9) and identify operations that need authorization checks
  - Ask questions to determine if SpiceDB is necessary:
    - Are there operations only certain roles can perform? (e.g., only VPs can change member status)
    - Does the hierarchical group structure (org → track → team) require permission inheritance?
    - Are there data access restrictions? (e.g., track leaders can only see their track's members)
  - Document authorization requirements in `docs/authorization-requirements.md`
  - **Make decision**: 
    - **YES, need SpiceDB**: Fine-grained permissions required, multiple roles, hierarchical access control → Continue to Task 11
    - **NO, skip SpiceDB**: Simple role check (admin vs member) can be done in n8n with Sheets lookup → Skip to Task 13

  **Decision Criteria**:
  - YES if:
    - Multiple permission levels (president > VP > track leader > team leader > member)
    - Hierarchical permission inheritance (team leader inherits track leader permissions)
    - Complex permission checks (e.g., "Can user X edit member Y's data?")
  - NO if:
    - Simple admin check (is user in admin list?)
    - Binary permissions (can do X or can't do X)
    - Low security requirements (club internal tool)

  **Must NOT do**:
  - Don't implement SpiceDB "just because it's cool" (only if truly needed)
  - Don't skip if genuinely needed (insecure system is worse than no system)

  **Tools Used**: Documentation, analysis (no code)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requirements analysis and documentation task
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**:
    - N/A - decision-making task

  **Parallelization**:
  - **Can Run In Parallel**: NO (decision point affects next tasks)
  - **Parallel Group**: Sequential
  - **Blocks**: Tasks 11, 12 (decision determines if they run)
  - **Blocked By**: Tasks 6-9 (need workflows complete to analyze)

  **References**:

  **Authorization Patterns**:
  - Role-based access control (RBAC) basics: Simple role → permission mapping
  - Hierarchical RBAC: Role inheritance (admin inherits from user)
  - Attribute-based access control (ABAC): Complex rules based on attributes

  **SpiceDB Use Cases**:
  - When to use Zanzibar-style authorization: Multi-tenant, hierarchical relationships, fine-grained permissions
  - When NOT to use: Simple role checks, low user count, minimal security requirements

  **Alternative: Simple Authorization in n8n**:
  - Store admin emails in Sheets `admins` tab
  - n8n workflow: Lookup user email in `admins` tab → if found, allow operation

  **Why Each Reference Matters**:
  - Understanding auth patterns prevents over-engineering
  - Use case analysis ensures SpiceDB is actually needed (not just trendy tech)

  **Acceptance Criteria**:

  **Manual Execution Verification**:
  - [ ] Document created: `docs/authorization-requirements.md`
  - [ ] Document lists operations needing authorization (e.g., "Change member status", "Edit fee amount", "Delete member")
  - [ ] Document lists roles needed (e.g., "President", "Vice President", "Track Leader", "Team Leader", "Member")
  - [ ] Document includes decision matrix:
    - Operation X requires role Y
    - Role hierarchy defined (President > VP > Track Leader > Member)
  - [ ] **DECISION RECORDED** in document header:
    - "SpiceDB Required: YES/NO"
    - Justification: [reason based on analysis]

  **Decision Outcome:**
  - [ ] If YES → Update todos to mark Task 11, 12 as "pending" (will execute)
  - [ ] If NO → Update todos to mark Task 11, 12 as "cancelled" (skip to Task 13)

  **Evidence Required**:
  - [ ] `docs/authorization-requirements.md` file exists with complete analysis
  - [ ] Decision clearly documented with justification

  **Commit**: YES
  - Message: `docs(auth): analyze authorization requirements and make decision`
  - Files: `docs/authorization-requirements.md`
  - Pre-commit: Peer review of decision (if possible)

  **Estimated Effort**: Small (1-2h)

---

- [ ] **11. FastAPI + SpiceDB Integration Setup** *(ONLY IF Task 10 Decision = YES)*

  **What to do**:
  - Create FastAPI project structure:
    - `src/bcsdlab_internal/` (package name for BCSDLab Internal system)
    - `src/bcsdlab_internal/main.py` (FastAPI app entry point)
    - `src/bcsdlab_internal/api/` (API routes)
    - `src/bcsdlab_internal/core/` (config, dependencies)
    - `src/bcsdlab_internal/services/` (SpiceDB client wrapper)
    - `src/bcsdlab_internal/schemas/` (Pydantic models)
  - Set up FastAPI with basic endpoints:
    - `POST /api/v1/auth/check` - Check if user has permission for operation
    - `GET /api/v1/health` - Health check endpoint
  - Add SpiceDB to Docker Compose:
    - SpiceDB service with PostgreSQL backend
    - Migrate SpiceDB schema (define relationships: user, organization, track, team, member)
  - Integrate SpiceDB Python client (`authzed-py`)
  - Create SpiceDB schema based on hierarchical group structure:
    - organization → track → team relationships
    - Roles: president, vice_president, track_leader, team_leader, member
  - Test permission check: "Can user X (president) edit member Y's status?" → YES
  - Document FastAPI + SpiceDB setup in `docs/fastapi-setup.md`

  **Must NOT do**:
  - Don't create CRUD endpoints for members/fees (that's n8n's job via Sheets)
  - Don't build full authentication (just authorization checks)
  - Don't overcomplicate schema (start with basic org → track → team hierarchy)

  **Tools Used**: FastAPI (Python), SpiceDB, Docker Compose, authzed-py library

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward FastAPI setup with library integration
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - standard backend task

  **Parallelization**:
  - **Can Run In Parallel**: NO (blocks Task 12)
  - **Parallel Group**: Sequential (must complete before Task 12)
  - **Blocks**: Task 12 (n8n needs FastAPI running to call)
  - **Blocked By**: Task 10 (decision must be YES)

  **References**:

  **FastAPI Project Setup**:
  - FastAPI official docs: `https://fastapi.tiangolo.com/tutorial/` - Project structure, dependency injection
  - Pydantic models: `https://docs.pydantic.dev/` - Request/response schemas

  **SpiceDB Integration**:
  - authzed-py library: `https://github.com/authzed/authzed-py` - Python client for SpiceDB
  - SpiceDB schema language: `https://docs.authzed.com/reference/schema-lang` - Define relationships and permissions
  - SpiceDB Docker setup: `https://authzed.com/docs/spicedb/installing` - Running SpiceDB with Docker

  **Schema Design for Hierarchical Groups**:
  - Example schema (from research):
    ```
    definition organization {
      relation admin: user
      relation member: user
      permission view = member + admin
      permission edit = admin
    }
    
    definition track {
      relation parent: organization
      relation leader: user
      relation member: user
      permission view = member + leader + parent->admin
      permission edit = leader + parent->admin
    }
    
    definition team {
      relation parent: track
      relation leader: user
      relation member: user
      permission view = member + leader + parent->leader + parent->parent->admin
      permission edit = leader + parent->leader + parent->parent->admin
    }
    ```

  **FastAPI + SpiceDB Pattern**:
  - Create SpiceDB client wrapper service
  - Endpoint receives: user_id, resource_type, resource_id, operation (view/edit/delete)
  - Query SpiceDB: `CheckPermission(user_id, operation, resource_type:resource_id)`
  - Return: 200 OK (allowed) or 403 Forbidden (denied)

  **Why Each Reference Matters**:
  - authzed-py docs show exact API for permission checks (critical for correctness)
  - Schema language reference defines permission inheritance (models hierarchical structure)
  - FastAPI patterns ensure clean dependency injection (SpiceDB client as dependency)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Docker Setup:**
  - [ ] Update `docker-compose.yml` to include FastAPI and SpiceDB services
  - [ ] Command: `docker compose up -d`
  - [ ] Expected: All services running (n8n, FastAPI, SpiceDB, PostgreSQL for SpiceDB)
  - [ ] Command: `curl http://localhost:8000/api/v1/health`
  - [ ] Expected: `{"status": "healthy", "spicedb": "connected"}`

  **SpiceDB Schema:**
  - [ ] SpiceDB schema file created: `spicedb/schema.zed`
  - [ ] Schema defines: organization, track, team definitions with hierarchical permissions
  - [ ] Command: `docker compose exec spicedb zed schema write < spicedb/schema.zed`
  - [ ] Expected: Schema applied successfully

  **Permission Check Endpoint:**
  - [ ] Request: `curl -X POST http://localhost:8000/api/v1/auth/check -H "Content-Type: application/json" -d '{"user_id": "president@bcsdlab.com", "operation": "edit", "resource": "member:123"}'`
  - [ ] Expected response: `{"allowed": true}`
  - [ ] Test deny case: User without permission
  - [ ] Expected response: `{"allowed": false}`

  **Integration Test:**
  - [ ] Add test relationships to SpiceDB (organization:bcsdlab, user:president@bcsdlab.com as admin)
  - [ ] Verify permission check works end-to-end

  **Evidence Required**:
  - [ ] Screenshot of FastAPI docs page at `http://localhost:8000/docs`
  - [ ] Screenshot of successful permission check response
  - [ ] `spicedb/schema.zed` file committed
  - [ ] `docs/fastapi-setup.md` with setup instructions

  **Commit**: YES
  - Message: `feat(auth): add FastAPI + SpiceDB authorization service`
  - Files: `src/bcsdlab_internal/`, `spicedb/schema.zed`, `docker-compose.yml` (updated), `docs/fastapi-setup.md`, `pyproject.toml` (if using Poetry) or `requirements.txt`
  - Pre-commit: `pytest tests/` (if tests written), manual API test

  **Estimated Effort**: Large (6-10h)

---

- [ ] **12. n8n Authorization Workflow Integration** *(ONLY IF Task 11 Complete)*

  **What to do**:
  - Update sensitive n8n workflows to call FastAPI authorization endpoint before executing
  - Target workflows:
    - "Member Status Transition" (Task 9) → Check if requester can change status
    - "Fee Payment Processing" (Task 6) → Check if requester can record payment (if admin-triggered)
  - Add HTTP Request node in n8n:
    - Method: POST
    - URL: `http://fastapi:8000/api/v1/auth/check`
    - Body: `{"user_id": "{{$json.requester_email}}", "operation": "edit", "resource": "member:{{$json.member_id}}"}`
  - Add IF node after authorization check:
    - If `{{$json.allowed}} === true` → Continue workflow
    - If `{{$json.allowed}} === false` → Send error notification, stop workflow
  - Update Google Forms to include "Requester Email" field (who is making the request)
  - Test authorization: Submit form as admin (allowed) vs regular member (denied)
  - Document authorization workflow pattern in `docs/workflow-guide.md`

  **Must NOT do**:
  - Don't add authorization to all workflows (only sensitive operations)
  - Don't hardcode user roles in n8n (always call FastAPI/SpiceDB)
  - Don't fail silently (log authorization failures clearly)

  **Tools Used**: n8n (HTTP Request node), FastAPI endpoint from Task 11

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Modifying existing workflows with authorization logic
  - **Skills**: None specific
  - **Skills Evaluated but Omitted**:
    - N/A - workflow modification task

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 11)
  - **Parallel Group**: Sequential
  - **Blocks**: None (final integration task)
  - **Blocked By**: Task 11 (needs FastAPI + SpiceDB running)

  **References**:

  **n8n HTTP Request Node**:
  - HTTP Request node: `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/` - Making API calls from workflows
  - Authentication: None needed (internal Docker network)

  **Workflow Modification Pattern**:
  - Before: Form → Process Data → Update Sheets
  - After: Form → Extract Requester → Call FastAPI Auth → IF Allowed → Process Data → Update Sheets
  - Error branch: IF Denied → Log Error → Send Rejection Notification

  **SpiceDB Permission Model**:
  - User ID source: Extract from form field "Requester Email"
  - Resource ID: Member being edited (from `members` Sheets lookup)
  - Operation: "edit", "view", or "delete" depending on workflow

  **Why Each Reference Matters**:
  - HTTP Request node is only way for n8n to call external APIs (critical for auth)
  - Workflow modification pattern ensures authorization is enforced before sensitive operations
  - SpiceDB model must match FastAPI endpoint expectations (consistent resource naming)

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Setup Test Permissions:**
  - [ ] Add relationships to SpiceDB via FastAPI or direct SpiceDB API:
    - organization:bcsdlab#admin@president@bcsdlab.com (President has admin on org)
    - member:test-member-123 (Test member exists)
  - [ ] Verify with permission check: President can edit member → allowed=true

  **Test Authorized Request:**
  - [ ] Update "Member Status Transition" form to include "Requester Email" field
  - [ ] Submit form:
    - Requester Email: president@bcsdlab.com
    - Member Email: test-member@test.com
    - New Status: Regular
  - [ ] Workflow executes successfully (authorization passes)
  - [ ] Google Sheets `members` tab shows status updated
  - [ ] `workflow_logs` shows "Authorization: allowed, Requester: president@bcsdlab.com"

  **Test Denied Request:**
  - [ ] Submit same form with:
    - Requester Email: random-user@test.com (not in SpiceDB as admin)
    - Member Email: test-member@test.com
  - [ ] Expected: Workflow stops at authorization check
  - [ ] `workflow_logs` shows "Authorization: denied, Requester: random-user@test.com"
  - [ ] Email sent to random-user@test.com: "You do not have permission to perform this action"
  - [ ] Google Sheets `members` tab NOT updated (status unchanged)

  **Evidence Required**:
  - [ ] Screenshot of updated n8n workflow showing HTTP Request node for auth check
  - [ ] Screenshot of successful authorized execution log
  - [ ] Screenshot of denied execution log with error message
  - [ ] Updated workflow JSON exported to `workflows/member-status-transition.json` (version 2)

  **Commit**: YES
  - Message: `feat(workflow): integrate SpiceDB authorization checks`
  - Files: `workflows/member-status-transition.json` (updated), `docs/workflow-guide.md` (update with auth pattern)
  - Pre-commit: Test both allowed and denied scenarios

  **Estimated Effort**: Medium (3-5h)

---

### Final Task: Documentation & Deployment

---

- [ ] **13. Comprehensive Documentation & Deployment Guide**

  **What to do**:
  - Create `README.md` for the repository:
    - Project overview (what is BCSDLab INTERNAL)
    - Architecture diagram (n8n + Google Workspace + optional FastAPI/SpiceDB)
    - Quick start guide (how to run locally with Docker Compose)
  - Create `docs/deployment.md`:
    - Production deployment steps (Docker Compose on EC2)
    - Environment variables configuration
    - Backup strategy (Google Sheets already serves as backup, but document this)
    - Monitoring recommendations (n8n has built-in execution logs)
  - Create `docs/workflows-index.md`:
    - List all workflows with descriptions
    - How to import workflow JSON files into n8n
    - How to activate/deactivate workflows
    - Troubleshooting common issues (Sheets API rate limits, webhook not firing, etc.)
  - Create `docs/emergency-procedures.md`:
    - What to do if EC2 dies (access Google Sheets directly, manual processes)
    - How to recover n8n workflows (import from JSON)
    - Contact list for Google Workspace admin, EC2 admin
  - Update all existing docs with final information
  - Create `CONTRIBUTING.md` if applicable (for club developers)

  **Must NOT do**:
  - Don't write redundant information (cross-reference other docs instead)
  - Don't create docs for features not implemented (only document what exists)
  - Don't skip operational docs (emergency procedures are critical)

  **Tools Used**: Markdown documentation only

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Pure documentation task
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**:
    - N/A - writing task

  **Parallelization**:
  - **Can Run In Parallel**: NO (final task after all others)
  - **Parallel Group**: Sequential (must be last)
  - **Blocks**: None (final deliverable)
  - **Blocked By**: All other tasks (needs complete system to document)

  **References**:

  **Documentation Best Practices**:
  - README template: `https://github.com/othneildrew/Best-README-Template` - Structure and sections
  - Deployment docs: Include exact commands, not just descriptions
  - Emergency procedures: Step-by-step checklists, not paragraphs

  **Architecture Diagram Tools**:
  - Mermaid.js for diagrams in Markdown: `https://mermaid.js.org/` - Render diagrams from text
  - Example:
    ```mermaid
    graph LR
      A[Google Forms] --> B[n8n]
      B --> C[Google Sheets]
      B --> D[Slack]
      B --> E[Email]
      B --> F[FastAPI]
      F --> G[SpiceDB]
    ```

  **Why Each Reference Matters**:
  - README template ensures all critical sections included (installation, usage, troubleshooting)
  - Mermaid diagrams are version-controllable and render on GitHub (no external image files)
  - Emergency procedures checklist format ensures nothing is missed in crisis

  **Acceptance Criteria**:

  **Manual Execution Verification**:

  **Documentation Completeness Check:**
  - [ ] `README.md` exists and includes:
    - Project title and description
    - Architecture diagram (Mermaid or image)
    - Prerequisites (Docker, Docker Compose, Google Workspace account)
    - Quick start: `git clone` → `docker compose up` → access n8n UI
    - Links to detailed docs
  - [ ] `docs/deployment.md` exists with production deployment steps
  - [ ] `docs/workflows-index.md` lists all workflows from Tasks 6-9, 12
  - [ ] `docs/emergency-procedures.md` includes:
    - Checklist: What to do if EC2 is down
    - How to access Google Sheets directly
    - How to manually process fee payments
    - Who to contact for help
  - [ ] All doc links are valid (no broken references)

  **New User Test (Simulate new developer joining):**
  - [ ] Fresh clone of repository (or ask colleague to try)
  - [ ] Follow README quick start instructions
  - [ ] Expected: Can bring up n8n, access UI, see workflows (imported from JSON)
  - [ ] Any missing steps? → Update README

  **Evidence Required**:
  - [ ] All documentation files exist and pass markdown linter (if available)
  - [ ] Screenshot of README rendered on GitHub (with architecture diagram visible)
  - [ ] Peer review of docs (if another club member can review)

  **Commit**: YES
  - Message: `docs: add comprehensive documentation and deployment guide`
  - Files: `README.md`, `docs/deployment.md`, `docs/workflows-index.md`, `docs/emergency-procedures.md`, `CONTRIBUTING.md` (optional)
  - Pre-commit: Spell check, markdown lint

  **Estimated Effort**: Medium (3-4h)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(infra): add Docker Compose setup for n8n` | docker-compose.yml, .env.example, .gitignore | docker compose up → n8n UI loads |
| 2 | `docs(setup): add Google Workspace API setup guide` | docs/google-api-setup.md, .env.example, .gitignore | Service account JSON works |
| 3 | `docs(schema): add Google Sheets database schema design` | docs/sheets-schema.md, .env.example | Sheets tabs created |
| 4 | `feat(n8n): add Google Sheets integration test workflow` | workflows/test-sheets-connection.json, docs/n8n-setup.md | Workflow executes successfully |
| 5 | `feat(forms): create fee payment and member registration forms` | docs/forms-guide.md | Form submissions appear in Sheets |
| 5.5 | `feat(migration): migrate existing Sheets data to new schema` | docs/migration-log.md, workflows/data-migration-onetime.json (if used) | Migrated data verified in new Sheets |
| 6 | `feat(workflow): add fee payment processing workflow` | workflows/fee-payment-processing.json, docs/workflow-guide.md | Form → Sheets → updated correctly (uses migrated data) |
| 7 | `feat(workflow): add scheduled fee payment reminder` | workflows/fee-payment-reminder.json, docs/workflow-guide.md | Reminder sent to unpaid members |
| 8 | `feat(workflow): add member registration and onboarding automation` | workflows/member-onboarding.json, docs/workflow-guide.md | New member added to all systems |
| 9 | `feat(workflow): add member status transition workflow` | workflows/member-status-transition.json, docs/workflow-guide.md, docs/forms-guide.md | Status transitions work correctly |
| 10 | `docs(auth): analyze authorization requirements and make decision` | docs/authorization-requirements.md | Decision documented |
| 11 | `feat(auth): add FastAPI + SpiceDB authorization service` | src/bcsdlab_internal/, spicedb/schema.zed, docker-compose.yml, docs/fastapi-setup.md | Permission check API works |
| 12 | `feat(workflow): integrate SpiceDB authorization checks` | workflows/member-status-transition.json (v2), docs/workflow-guide.md | Auth allows/denies correctly |
| 13 | `docs: add comprehensive documentation and deployment guide` | README.md, docs/deployment.md, docs/workflows-index.md, docs/emergency-procedures.md | New dev can follow README successfully |

---

## Success Criteria

### Verification Commands

**Bring up entire system:**
```bash
docker compose up -d  # Expected: All services start (n8n, FastAPI if enabled, SpiceDB if enabled)
curl http://localhost:5678  # Expected: n8n login page (200 OK)
curl http://localhost:8000/api/v1/health  # Expected: {"status": "healthy"} (if FastAPI enabled)
```

**Test end-to-end fee payment workflow:**
```bash
# 1. Submit fee payment form via browser (Google Form from Task 5)
# 2. Wait 2 minutes for n8n trigger
# 3. Check Google Sheets:
#    - fee_payment_responses tab has submission
#    - fees tab has new record
#    - members tab shows payment_status updated
# 4. Check workflow_logs tab for success entry
```

**Test scheduled reminder:**
```bash
# 1. Set test members with unpaid status
# 2. Manually execute "Fee Payment Reminder" workflow in n8n
# 3. Verify Slack/Email notifications sent
# 4. Check workflow_logs for summary (X reminders sent)
```

### Final Checklist

**Must Have (MVP Core):**
- [x] n8n running and connected to Google Workspace
- [x] Google Sheets with structured data (members, fees, groups, events, workflow_logs)
- [x] At least 3 working workflows (fee payment, reminder, member onboarding)
- [x] Docker Compose setup for easy deployment
- [x] Basic documentation (README, workflow guide, emergency procedures)

**Must NOT Have (Guardrails Met):**
- [x] No complex database sync (Sheets is database, no sync needed)
- [x] No FastAPI as main backend (only optional for authorization)
- [x] No premature optimization (simple workflows, can refactor later)
- [x] No over-abstraction (readable n8n workflows, not code spaghetti)

**Optional (If Implemented):**
- [ ] FastAPI + SpiceDB authorization (Tasks 11-12) - only if Task 10 decision = YES
- [ ] Slack integration in all workflows (vs just email)
- [ ] Google Calendar/Drive integration in onboarding workflow

**Operational Readiness:**
- [ ] Emergency procedures documented (manual Sheets editing process)
- [ ] Backup strategy clear (Google Sheets IS the backup)
- [ ] Monitoring in place (n8n execution logs)
- [ ] Rollback plan (n8n workflow version control via JSON exports)

---

## Additional Notes

### Key Architectural Decisions Made

1. **Google Workspace as Platform**: Sheets is database, Forms are input, Docs are output. No sync needed.

2. **n8n as Primary Engine**: All business logic in visual workflows. FastAPI only for what n8n can't do (SpiceDB auth).

3. **Resilience via Google Workspace**: Even if EC2 dies, humans can access Sheets, edit manually, submit Forms. Operations continue.

4. **Authorization is Optional**: Only implement FastAPI + SpiceDB (Tasks 11-12) if Task 10 analysis shows it's genuinely needed. Simple admin checks can be done in n8n with Sheets lookup.

5. **PostgreSQL/MongoDB Likely Unused**: Default to Google Sheets unless proven inadequate. Don't add databases "just in case."

### Performance Considerations

- **Google Sheets API Rate Limits**: 300 requests/min per project. Use batch operations where possible.
- **n8n Execution Queue**: For high-volume workflows, enable queue mode with Redis.
- **Webhook vs Polling**: Forms → n8n via Sheets trigger (polling) is simpler than Apps Script webhooks. Acceptable 1-2 min delay.

### Future Enhancements (Post-MVP)

- Calendar integration (Google Calendar events for meetings)
- URL shortening service (maybe not needed if Google Forms short links suffice)
- QR code generation (for check-ins, maybe using n8n HTTP Request to QR API)
- Report generation (Google Docs API to generate activity reports)
- Advanced notifications (granular Slack channels per track/team)

### Troubleshooting Tips

- **n8n workflow not triggering**: Check polling interval (default 2 min), verify Sheets trigger is activated
- **Sheets API quota exceeded**: Reduce workflow execution frequency, use batch operations
- **FastAPI can't reach SpiceDB**: Verify Docker network, check service names in compose file
- **Form submissions not appearing**: Check Sheets sharing permissions (service account must have Editor access)
