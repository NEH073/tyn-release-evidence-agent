# TYN Release Assessment - R2.4

**Overall decision: BLOCKED**

- Model: gemini-3.5-flash-lite
- Provider: Google Gemini
- Project: TYN
- Manifest: TYN-360
- Dataset: tyn-release-assessment-v2
- Commit: b7a91f2
- Prompt: p7
- Service: atlas-assistant
- Environment: production
- Requirements investigated: 12
- Total runtime: 265.92 seconds
- Input tokens: 123970
- Output tokens: 5888
- Total tokens: 129858

## Requirement decisions

### TYN-89 - PASS

Requirement ID: TYN-89
Requirement: [REQ-01] Automated regression tests (All automated regression cases must pass on the target build.)
Decision: PASS
Explanation: The target release context specifies release R2.4, commit b7a91f2, prompt p7, service atlas-assistant, and environment production. Linked evidence TYN-316 (REC-2081) records that QA Lead Priya Nair completed regression run REG-804 on the exact target build (release R2.4, commit b7a91f2, service atlas-assistant, environment production) with 146 of 146 mandatory regression cases passing. Although TYN-130 (REC-2299) reports an earlier regression run (REG-779) on an older commit (9c3e1aa) with failures, TYN-316 explicitly provides the target-scope verification matching the required build and demonstrates that all automated regression cases pass.
Evidence: 
- TYN-89 description & comments ([SOURCE_COMMENT:REQ-01:1-5])
- TYN-316 (REC-2081) comment [SOURCE_COMMENT:REC-2081:4]: QA Lead Priya Nair completed regression run REG-804 for release R2.4, commit b7a91f2, service atlas-assistant, environment production, showing 146 of 146 mandatory regression cases pass.
Outstanding verification: None.

### TYN-263 - FAIL

Requirement ID: TYN-263
Requirement: [REQ-02] Customer document isolation - Every isolation case must pass; any confirmed cross-customer document exposure blocks release.
Decision: FAIL
Explanation: Applicable target-scope QA evidence affirmatively demonstrates that the acceptance criterion failed on the target release build. Specifically, linked evidence record TYN-306 (Isolation retest ISO-318) for the target release R2.4, commit b7a91f2, service atlas-assistant in production records that customer ALPHA received document BETA-017, which belongs to customer BETA, explicitly proving a confirmed cross-customer document exposure on the target build.
Evidence:
- Jira issue TYN-263 (REQ-02): Customer document isolation requirement for release R2.4, commit b7a91f2, prompt p7, environment production, service atlas-assistant.
- Jira issue TYN-306 (REC-1001): Isolation retest ISO-318 for release R2.4, commit b7a91f2, service atlas-assistant, environment production. Comment [REC-1001:2] by QA Lead Priya Nair states: "Isolation retest ISO-318: release R2.4; commit b7a91f2; service atlas-assistant; environment production. Customer ALPHA received document BETA-017, which belongs to customer BETA. Reopening defect ISO-DEF-12."
Outstanding verification: None. Target-scope evidence affirmatively proves a failure of the acceptance criterion.

### TYN-225 - INSUFFICIENT_EVIDENCE

Requirement ID: TYN-225
Requirement: The approved quality evaluation must achieve at least 90 percent and match the deployed prompt p7.
Decision: INSUFFICIENT_EVIDENCE
Explanation: 
The requirement specifies that the approved quality evaluation must achieve at least 90 percent and match the deployed prompt `p7` for release `R2.4`, commit `b7a91f2`, service `atlas-assistant`, and environment `production`.
- Linked evidence record **TYN-214** (REC-1600) reports evaluation EVAL-61 with answer accuracy 91.0 percent, but it is for environment `staging` and commit `9c3e1aa` (wrong-scope).
- Linked evidence record **TYN-26** (REC-4323) reports evaluation EVAL-55 for release `R2.4`, commit `b7a91f2`, service `atlas-assistant`, and environment `production` with 96.2 percent accuracy, but comment 3 states: "Evaluation EVAL-55 harness configured with prompt bundle p6 (frozen on 2026-11-01)", which fails to match the required deployed prompt `p7`.
Therefore, there is no approved quality evaluation meeting both the >=90% accuracy threshold and matching the deployed prompt `p7` on the correct production target.
Evidence: 
- Jira Issue **TYN-225**: Description specifies Requirement ID `REQ-03`, target release `R2.4`, commit `b7a91f2`, prompt `p7`, environment `production`, service `atlas-assistant`. Acceptance criterion: "The approved quality evaluation must achieve at least 90 percent and match the deployed prompt p7."
- Jira Issue **TYN-214** (REC-1600): Comment 4 (`REC-1600:4`) by Priya Nair: "Evaluation EVAL-61: release R2.4; commit 9c3e1aa; service atlas-assistant; environment staging; prompt p7. Answer accuracy 91.0 percent." (Wrong scope: staging / different commit).
- Jira Issue **TYN-26** (REC-4323): Comment 3 (`REC-4323:3`) by Priya Nair: "Evaluation EVAL-55 harness configured with prompt bundle p6 (frozen on 2026-11-01)." and Comment 4 (`REC-4323:4`) by Priya Nair: "EVAL-55 completed: release R2.4; commit b7a91f2; service atlas-assistant; environment production. Answer accuracy 96.2 percent across 500 graded questions. Approved." (Wrong prompt bundle: p6 instead of p7).
Outstanding verification: 
- An approved quality evaluation for release `R2.4`, commit `b7a91f2`, service `atlas-assistant`, environment `production` that specifically achieves at least 90 percent accuracy and matches the deployed prompt `p7`.

### TYN-53 - PASS

Requirement ID: TYN-53
Requirement: The production-equivalent target-build p95 response time must be at most 2.0 seconds.
Decision: PASS
Explanation: Linked evidence record TYN-150 (Performance run PERF-827) provides the exact required scope: release R2.4, commit b7a91f2, service atlas-assistant, environment production, and prompt p7. The QA Lead Priya Nair recorded a measured p95 latency of 1.40 seconds across 1000 requests, which satisfies the maximum threshold of 2.0 seconds.
Evidence: Jira issue TYN-53 and linked performance run TYN-150 (REC-6024), specifically comment [SOURCE_COMMENT:REC-6024:3] by Priya Nair: "Performance run PERF-827: release R2.4; commit b7a91f2; service atlas-assistant; environment production; prompt p7. Measured p95 latency 1.40 seconds across 1000 requests."
Outstanding verification: None

### TYN-352 - FAIL

Requirement ID: TYN-352
Requirement: Mean model cost per successful request must be at most USD 0.012 using the exercise rate card.
Decision: FAIL
Explanation: Linked evidence record TYN-224 (Cost run COST-881) for the target release R2.4, commit b7a91f2, service atlas-assistant, production environment, and prompt p7 measured a mean cost of USD 0.018 per successful request under the supplied rate card, retries included. This exceeds the maximum allowable threshold of USD 0.012 specified in requirement TYN-352.
Evidence: 
- TYN-352 description specifies: Target release R2.4, commit b7a91f2, prompt p7, environment production, service atlas-assistant; acceptance criterion: Mean model cost per successful request must be at most USD 0.012 using the exercise rate card.
- TYN-224 comment [REC-5716:2] by Priya Nair (QA Lead): "Cost run COST-881: release R2.4; commit b7a91f2; service atlas-assistant; environment production; prompt p7. Mean cost USD 0.018 per successful request under the supplied fictional rate card, retries included."
Outstanding verification: None. Target-scope evidence affirmatively demonstrates a failure of the acceptance criterion.

### TYN-73 - INSUFFICIENT_EVIDENCE

Requirement ID: TYN-73
Requirement: Security Owner Asha Rao must explicitly approve this release and commit for production.
Decision: INSUFFICIENT_EVIDENCE
Explanation: The requirement states that Security Owner Asha Rao must explicitly approve this release and commit for production. Reviewing the linked evidence record TYN-180 (REC-2828), Security Owner Asha Rao provided an approval on 2026-11-08 (comment [SOURCE_COMMENT:REC-2828:3]), but explicitly restricted the approval scope to staging, noting that "Production sign-off scheduled after the penetration-test window closes." A staging approval cannot approve production. Therefore, the required production security approval from Asha Rao is absent/insufficient.
Evidence: 
- Jira Issue TYN-73 ([REQ-06]): Requirement for production security approval by Security Owner Asha Rao for release R2.4, commit b7a91f2, service atlas-assistant, environment production.
- Jira Issue TYN-180 ([REC-2828]): Security approval record. Comment [SOURCE_COMMENT:REC-2828:3] shows Asha Rao approved release R2.4, commit b7a91f2, service atlas-assistant with the scope explicitly set to staging ("Approval scope: staging. Production sign-off scheduled after the penetration-test window closes.").
Outstanding verification: Explicit production security approval from Security Owner Asha Rao for release R2.4, commit b7a91f2, service atlas-assistant in production.

### TYN-329 - PASS

Requirement ID: TYN-329
Requirement: QA must verify that sensitive identifiers are redacted on the target build.
Decision: PASS
Explanation: 
The requirement TYN-329 ([REQ-07]) targets release R2.4, commit b7a91f2, prompt p7, service atlas-assistant, and production environment, requiring QA verification that sensitive identifiers are redacted. 
Linked evidence record TYN-396 ([REC-9745]) provides the QA retest for sensitive log redaction under the exact target release (R2.4), commit (b7a91f2), service (atlas-assistant), and environment (production). 
Although an initial test case (REDACT-870) failed due to customer phone numbers found unredacted in request logs (recorded in comment [SOURCE_COMMENT:REC-9745:3]), QA Lead Priya Nair explicitly recorded that REDACT-901 supersedes REDACT-870, confirming a retest on release R2.4, commit b7a91f2, service atlas-assistant, environment production where 28 of 28 redaction cases pass (recorded in comment [SOURCE_COMMENT:REC-9745:4]). 
This valid target-scope QA verification affirmatively proves the acceptance criterion.

Evidence:
- Jira Issue TYN-329 ([REQ-07]): Specifies the requirement for sensitive log redaction on release R2.4, commit b7a91f2, prompt p7, service atlas-assistant, production environment.
- Jira Issue TYN-396 ([REC-9745]): Engineering record for Redaction retest - Sensitive log redaction.
  - Comment [SOURCE_COMMENT:REC-9745:4] (QA Lead Priya Nair): "REDACT-901 explicitly supersedes REDACT-870. Retest on release R2.4; commit b7a91f2; service atlas-assistant; environment production: 28 of 28 redaction cases pass."

Outstanding verification:
None.

### TYN-48 - FAIL

Requirement ID: TYN-48
Requirement: When an answer is escalated, a handoff must reach the support queue, including its linked delivery dependency.
Decision: FAIL
Explanation: The directly linked engineering record TYN-342 notes that handoff delivery relies on the queue-adapter work. Following this linked dependency to TYN-76 (Queue adapter verification - Human handoff delivery), QA Lead Priya Nair recorded on 2026-11-08 that test HND-77 for release R2.4, commit b7a91f2, service atlas-assistant, in the production environment failed: 0 of 12 escalated conversations reached the support queue because the queue adapter drops them, and defect HND-DEF-4 remains open. This demonstrates an affirmative failure of the acceptance criterion on the target build.
Evidence:
- Jira issue TYN-48 ([REQ-08] Human handoff delivery): requirement specifying acceptance criterion "When an answer is escalated, a handoff must reach the support queue, including its linked delivery dependency."
- Jira issue TYN-342 ([REC-4076] Handoff implementation - Human handoff delivery): linked engineering record stating "Handoff UI implemented for release R2.4. Message delivery relies on the linked queue-adapter work."
- Jira issue TYN-76 ([REC-9635] Queue adapter verification - Human handoff delivery): linked queue-adapter dependency record, with comment from QA Lead Priya Nair (2026-11-08): "Handoff delivery test HND-77: release R2.4; commit b7a91f2; service atlas-assistant; environment production. 0 of 12 escalated conversations reached the support queue; the queue adapter drops them. Defect HND-DEF-4 status: open."
Outstanding verification: None.

### TYN-143 - INSUFFICIENT_EVIDENCE

Requirement ID: TYN-143
Requirement: An approved rollback rehearsal must succeed on the target release and production configuration.
Decision: INSUFFICIENT_EVIDENCE
Explanation: The requirement (REQ-09) has two linked QA evidence records:
1. TYN-105 (REC-6011): QA Lead Priya Nair reports Rollback rehearsal RB-401 for release R2.4, commit b7a91f2, service atlas-assistant, production environment: previous version restored in 6 minutes; health probes pass; no data loss observed.
2. TYN-174 (REC-6198): QA Lead Arjun Mehta reports Rollback rehearsal RB-402 for release R2.4, commit b7a91f2, service atlas-assistant, production environment: restore completed but 214 session records written during the window were lost; rehearsal FAILED.

These are equally authoritative current QA records describing rollback rehearsals for the target build that conflict directly (one reports success with no data loss, while the second reports failure due to data loss of 214 session records), and neither record explicitly supersedes or resolves the other. Under the decision rules for conflicting QA results where equally authoritative current records conflict without resolution, the assessment must be classified as INSUFFICIENT_EVIDENCE.
Evidence: 
- Jira Issue TYN-143 (REQ-09)
- Jira Issue TYN-105 (REC-6011, comment [SOURCE_COMMENT:REC-6011:4]): Rollback rehearsal RB-401 succeeded with no data loss.
- Jira Issue TYN-174 (REC-6198, comment [SOURCE_COMMENT:REC-6198:2]): Rollback rehearsal RB-402 failed with loss of 214 session records.
Outstanding verification: Resolution of the conflicting QA results between Rollback rehearsal RB-401 (TYN-105) and Rollback rehearsal RB-402 (TYN-174), with an explicit superseding record or authoritative resolution clarifying whether the rollback rehearsal succeeded without data loss on the target production release.

### TYN-57 - PASS

Requirement ID: TYN-57
Requirement: The target build must pass all 60 mandatory document parsing cases.
Decision: PASS
Explanation: Linked evidence record TYN-9 (Source ID: REC-9611) documents the document parsing verification for release R2.4, commit b7a91f2, service atlas-assistant, in the production environment. QA Lead Priya Nair recorded in comment 5 (SOURCE_COMMENT:REC-9611:5) that test PARSE-622 supersedes the earlier PARSE-601 test result, and confirms that 60 of 60 mandatory parsing cases pass on the target release, commit, service, and environment. This directly satisfies the acceptance criterion.
Evidence: 
- Jira Issue TYN-57 description specifies requirement REQ-10: "The target build must pass all 60 mandatory document parsing cases" for release R2.4, commit b7a91f2, prompt p7, environment production, service atlas-assistant.
- Linked issue TYN-9 (Source ID: REC-9611), comment 5 (SOURCE_COMMENT:REC-9611:5): Recorded event 2026-11-08T14:00:00+05:30 by Priya Nair (QA Lead) stating: "PARSE-622 supersedes PARSE-601. Retest on release R2.4; commit b7a91f2; service atlas-assistant; environment production: 60 of 60 mandatory parsing cases pass."
Outstanding verification: None.

### TYN-162 - INSUFFICIENT_EVIDENCE

Requirement ID: TYN-162
Requirement: QA must verify keyboard navigation and focus handling for the handoff interface on the target release.
Decision: INSUFFICIENT_EVIDENCE
Explanation: The requirement (REQ-11) states that QA must verify keyboard navigation and focus handling for the handoff interface on the target release (Release: R2.4, Commit: b7a91f2, Prompt: p7, Service: atlas-assistant, Environment: production). Linked evidence TYN-102 (REC-8801) contains a QA verification record from Priya Nair (QA Lead), but it corresponds to release R2.3, commit 42d09ce, service atlas-assistant, and environment production, which is a different release/commit version than the required target release context (R2.4, commit b7a91f2). Another linked evidence record TYN-259 (REC-8515) is merely an implementation claim by developer Sam Patel rather than a verified QA test result on the target release context. Therefore, valid target-scope QA verification for R2.4 is absent.
Evidence: 
- Jira issue TYN-162 ([REQ-11] Accessible keyboard handoff): Target release R2.4, commit b7a91f2, prompt p7, service atlas-assistant, environment production.
- Jira issue TYN-102 ([REC-8801] Keyboard navigation QA - Accessible keyboard handoff): Contains QA comment dated 2026-10-28 for release R2.3 and commit 42d09ce (wrong-scope release context).
- Jira issue TYN-259 ([REC-8515] Keyboard implementation - Accessible keyboard handoff): Contains developer implementation claim by Sam Patel, but no QA verification for R2.4.
Outstanding verification: QA verification of keyboard navigation and focus handling for the handoff interface specifically on release R2.4, commit b7a91f2, service atlas-assistant, and production environment.

### TYN-400 - FAIL

Requirement ID: TYN-400
Requirement: Every mandatory streaming case must complete without duplicate or missing final messages.
Decision: FAIL
Explanation: The applicable QA verification record REC-5957 (linked via TYN-318) for release R2.4, commit b7a91f2, service atlas-assistant, environment production, and prompt p7 explicitly documents a failed mandatory test case (STREAM-50 produced a duplicated final message, violating the acceptance criterion).
Evidence: Jira issue TYN-400 (Source ID: REQ-12) and linked evidence TYN-318 (Source ID: REC-5957), specifically QA Lead Priya Nair's comment in REC-5957: "Streaming run STREAM-731: release R2.4; commit b7a91f2; service atlas-assistant; environment production; prompt p7. 49 of 50 cases pass. STREAM-50 produced a duplicated final message."
Outstanding verification: None.

## Decision summary

- PASS: 4
- FAIL: 4
- INSUFFICIENT_EVIDENCE: 4

## Execution metrics

- Model: gemini-3.5-flash-lite
- Provider: Google Gemini
- Runtime: 265.92 seconds
- Input tokens: 123970
- Output tokens: 5888
- Total tokens: 129858
- Token usage records: 41
