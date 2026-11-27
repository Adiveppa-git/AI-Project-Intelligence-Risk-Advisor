// Sample project documentation presets for easy 1-click testing in frontend

export const SAMPLE_DOCS = [
  {
    id: 'charter',
    name: 'Official Project Charter (ECAP)',
    title: 'Enterprise Cloud Analytics Platform (ECAP)',
    format: 'PDF',
    type: 'pdf',
    filename: 'project_charter_ecap.pdf',
    description: 'Enterprise charter with objectives, deliverables, milestones, deadlines, and governance.',
    text: `Project Title: Enterprise Cloud Analytics Platform (ECAP)
Document Type: Official Project Charter & Architecture Specification
Version: 1.0 | Date: 2026-06-01
Sponsor: Enterprise Architecture Review Board

1. Executive Summary & Project Purpose
The Enterprise Cloud Analytics Platform (ECAP) modernizes telemetry data collection and distributed data warehouse operations.

2. Project Objectives
- Build a real-time event-driven telemetry pipeline processing 50,000 events/second.
- Implement zero-trust role-based access control (RBAC) gateway for API clients.
- Provide real-time operational risk intelligence dashboards for executive leadership.
- Enable automated streaming synchronization into Snowflake warehouse.

3. Key Expected Deliverables and Milestones
- Deliverable 1: Cloud Telemetry Pipeline (Owner: Alice Chen, Deadline: 2026-08-15)
- Deliverable 2: Unified RBAC Gateway (Owner: Bob Martinez, Deadline: 2026-09-30)
- Deliverable 3: Real-Time Dashboard (Owner: Carol Vance, Deadline: 2026-11-20)
- Deliverable 4: Data Warehouse Sync (Owner: David Kim, Deadline: 2026-12-01)
- Milestone 1: Architectural Foundation (Target Date: 2026-08-30, Owner: Alice Chen)
- Milestone 2: Security Sign-off (Target Date: 2026-10-15, Owner: Bob Martinez)
- Milestone 3: Production Rollout (Target Date: 2026-12-10, Owner: David Kim)

4. Scope Boundaries
In-Scope: Kubernetes clusters, Kafka streaming, OAuth2 RBAC gateway, Snowflake synchronization.
Out-of-Scope: Legacy mainframe hardware, native mobile applications, public third-party endpoints.

5. Project Governance and Approvals
Project Lead: Alice Chen. Security Lead: Bob Martinez. Frontend Lead: Carol Vance. DevOps Lead: David Kim.
Approved Initial Budget Allocation: $250,000.`,
  },
  {
    id: 'meeting_notes',
    name: 'Sprint 14 Sync & Risk Review',
    title: 'Sprint 14 Retrospective & Technical Sync',
    format: 'TXT',
    type: 'txt',
    filename: 'sprint_14_retrospective.txt',
    description: 'Sprint 14 technical sync containing active blockers, pending decisions, and action items.',
    text: `# Meeting Notes: Sprint 14 Technical Sync and Risk Review
Date: 2026-09-18
Attendees: Alice Chen, Bob Martinez, Carol Vance, David Kim

## Current Blockers
- Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
- Blocker 2: Database migration scripts failing on staging cluster due to schema mismatch with legacy tables.
- Blocker 3: Staging cluster environment is experiencing frequent memory out-of-bounds crashes, halting integration tests.

## Pending Decisions
- Decision 1: Pending decision on selecting ClickHouse vs Snowflake for warm telemetry storage tier (Decision Maker: David Kim, Deadline: 2026-09-25).
- Decision 2: Pending decision regarding Kafka partition sizing and retention policy sign-off (Decision Maker: Alice Chen, Deadline: 2026-09-28).

## Unresolved Issues
- Issue: Intermittent network latency spikes exceeding 1200ms when querying cross-region replicas.
- Issue: Incomplete test coverage on token refresh failure modes.
- Issue: Flaky integration tests in the continuous delivery pipeline.

## Delayed Activities
- Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.
- Activity: Frontend telemetry chart rendering is behind schedule due to missing API specification.

## Action Items
- Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
- Action Item 2: Alice Chen to profile memory usage in telemetry worker pods by 2026-09-24 (Priority: High)
- Action Item 3: Investigate failing database migration scripts on staging (Assigned to: Unassigned, Deadline: 2026-09-22, Priority: High)
- Action Item 4: Carol Vance to mock dashboard response models by 2026-09-28 (Priority: Medium)
- Action Item 5: David Kim to configure automated pod restart policies by 2026-09-26 (Priority: Medium)
- Action Item 6: Clean up stale test accounts in staging database (Assigned to: Unassigned, Deadline: 2026-09-30, Priority: Low)`,
  },
  {
    id: 'progress_report',
    name: 'Monthly Progress Report',
    title: 'Q3 Enterprise Risk & Progress Report',
    format: 'DOCX',
    type: 'docx',
    filename: 'progress_report_q3.docx',
    description: 'Executive report with schedule delay warnings, budget overruns, and resource constraints.',
    text: `Enterprise Cloud Analytics Platform - Monthly Progress Report
Reporting Period: Q3 2026
Prepared by: Project Delivery Management

1. Executive Project Summary
The Enterprise Cloud Analytics Platform (ECAP) aims to build a modern telemetry and analytics infrastructure. Overall progress has slowed due to security review backlogs and technical dependencies.

2. Schedule and Delivery Risks
- Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.
- The target completion date of 2026-10-15 is at risk of slipping into November 2026.
- Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
- Dependency gap: The data warehouse sync pipeline depends on the completion of the Kafka brokers and schema validation module.

3. Budget and Resource Constraints
- Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.
- Resource constraint: The frontend engineering team is currently understaffed, creating a bandwidth bottleneck for dashboard widget completion.
- Shortage of senior site reliability engineers has contributed to deployment pipeline instability.

4. Technical Bottlenecks
- Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.`,
  },
  {
    id: 'task_list',
    name: 'Sprint Task Matrix',
    title: 'Sprint 14 Task & Milestone Matrix',
    format: 'CSV',
    type: 'csv',
    filename: 'task_matrix_sprint14.csv',
    description: 'Operational task list tracking IDs, owners, priorities, statuses, deadlines, and blocker notes.',
    text: `Task ID,Task Name,Deliverable,Owner,Priority,Status,Deadline,Dependencies,Notes
TSK-101,Deploy Kafka Ingestion Brokers,Cloud Telemetry Ingestion Pipeline,Alice Chen,High,Completed,2026-08-10,None,Deployed to Kubernetes cluster successfully
TSK-102,Configure RBAC OAuth Gateway,Unified RBAC Security Gateway,Bob Martinez,Critical,In progress,2026-09-28,SecOps Approval,Blocked by security compliance review
TSK-103,Design Executive Chart Components,Real-Time Executive Dashboard,Carol Vance,Medium,In progress,2026-10-15,None,UI mockups approved by stakeholders
TSK-104,Execute Staging Database Migration,Automated Data Warehouse Sync,Unassigned,High,Pending,2026-09-30,Kafka Pipeline,Migration tests failing on staging
TSK-105,Cloud Cost Containment Audit,Budget Optimization,David Kim,High,Pending,2026-10-05,None,Cloud spend exceeded budget by 22%
TSK-106,Automate Multi-Region Failover,Cloud Infrastructure,David Kim,Medium,Pending,2026-11-15,Kubernetes Clusters,Pending secondary cloud provider account setup
TSK-107,Perform Load and Stress Testing,System Reliability,Unassigned,Medium,Pending,2026-11-01,Staging Database Migration,Requires stable staging environment`,
  },
  {
    id: 'unified_corpus',
    name: 'Unified Project Corpus (All 4 Documents)',
    title: 'Enterprise Cloud Analytics Platform (Unified Corpus)',
    format: 'ALL',
    type: 'all',
    filename: 'unified_project_corpus.txt',
    description: 'Complete integrated enterprise corpus combining Charter (Scope), Sprint Notes (Blockers), Progress Report (Risks), and Task Matrix (Actions).',
    text: `Project Title: Enterprise Cloud Analytics Platform (ECAP)
Document Type: Official Project Charter & Architecture Specification
Version: 1.0 | Date: 2026-06-01
Sponsor: Enterprise Architecture Review Board

1. Executive Summary & Project Purpose
The Enterprise Cloud Analytics Platform (ECAP) modernizes telemetry data collection and distributed data warehouse operations.

2. Project Objectives
- Build a real-time event-driven telemetry pipeline processing 50,000 events/second.
- Implement zero-trust role-based access control (RBAC) gateway for API clients.
- Provide real-time operational risk intelligence dashboards for executive leadership.
- Enable automated streaming synchronization into Snowflake warehouse.

3. Key Expected Deliverables and Milestones
- Deliverable 1: Cloud Telemetry Pipeline (Owner: Alice Chen, Deadline: 2026-08-15)
- Deliverable 2: Unified RBAC Gateway (Owner: Bob Martinez, Deadline: 2026-09-30)
- Deliverable 3: Real-Time Dashboard (Owner: Carol Vance, Deadline: 2026-11-20)
- Deliverable 4: Data Warehouse Sync (Owner: David Kim, Deadline: 2026-12-01)
- Milestone 1: Architectural Foundation (Target Date: 2026-08-30, Owner: Alice Chen)
- Milestone 2: Security Sign-off (Target Date: 2026-10-15, Owner: Bob Martinez)
- Milestone 3: Production Rollout (Target Date: 2026-12-10, Owner: David Kim)

4. Scope Boundaries
In-Scope: Kubernetes clusters, Kafka streaming, OAuth2 RBAC gateway, Snowflake synchronization.
Out-of-Scope: Legacy mainframe hardware, native mobile applications, public third-party endpoints.

5. Project Governance and Approvals
Project Lead: Alice Chen. Security Lead: Bob Martinez. Frontend Lead: Carol Vance. DevOps Lead: David Kim.
Approved Initial Budget Allocation: $250,000.

# Meeting Notes: Sprint 14 Technical Sync and Risk Review
Date: 2026-09-18
Attendees: Alice Chen, Bob Martinez, Carol Vance, David Kim

## Current Blockers
- Blocker 1: Ingestion pipeline blocked by SecOps approval for external OAuth token exchange (Owner: Bob Martinez).
- Blocker 2: Database migration scripts failing on staging cluster due to schema mismatch with legacy tables.
- Blocker 3: Staging cluster environment is experiencing frequent memory out-of-bounds crashes, halting integration tests.

## Pending Decisions
- Decision 1: Pending decision on selecting ClickHouse vs Snowflake for warm telemetry storage tier (Decision Maker: David Kim, Deadline: 2026-09-25).
- Decision 2: Pending decision regarding Kafka partition sizing and retention policy sign-off (Decision Maker: Alice Chen, Deadline: 2026-09-28).

## Unresolved Issues
- Issue: Intermittent network latency spikes exceeding 1200ms when querying cross-region replicas.
- Issue: Incomplete test coverage on token refresh failure modes.
- Issue: Flaky integration tests in the continuous delivery pipeline.

## Delayed Activities
- Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.
- Activity: Frontend telemetry chart rendering is behind schedule due to missing API specification.

## Action Items
- Action Item 1: Bob Martinez to submit SecOps compliance exception ticket by 2026-09-20 (Priority: Critical)
- Action Item 2: Alice Chen to profile memory usage in telemetry worker pods by 2026-09-24 (Priority: High)
- Action Item 3: Investigate failing database migration scripts on staging (Assigned to: Unassigned, Deadline: 2026-09-22, Priority: High)
- Action Item 4: Carol Vance to mock dashboard response models by 2026-09-28 (Priority: Medium)
- Action Item 5: David Kim to configure automated pod restart policies by 2026-09-26 (Priority: Medium)
- Action Item 6: Clean up stale test accounts in staging database (Assigned to: Unassigned, Deadline: 2026-09-30, Priority: Low)

Enterprise Cloud Analytics Platform - Monthly Progress Report
Reporting Period: Q3 2026
Prepared by: Project Delivery Management

1. Executive Project Summary
The Enterprise Cloud Analytics Platform (ECAP) aims to build a modern telemetry and analytics infrastructure. Overall progress has slowed due to security review backlogs and technical dependencies.

2. Schedule and Delivery Risks
- Milestone 2 (Security Sign-off & Warehouse Integration) is delayed by 3 weeks due to pending SecOps compliance approvals and external API rate limits.
- The target completion date of 2026-10-15 is at risk of slipping into November 2026.
- Schedule delay: Security compliance review backlog is directly blocking the deployment of the OAuth Gateway.
- Dependency gap: The data warehouse sync pipeline depends on the completion of the Kafka brokers and schema validation module.

3. Budget and Resource Constraints
- Budget overrun: Cloud infrastructure expenditure exceeded budget by 22% due to over-provisioned staging clusters.
- Resource constraint: The frontend engineering team is currently understaffed, creating a bandwidth bottleneck for dashboard widget completion.
- Shortage of senior site reliability engineers has contributed to deployment pipeline instability.

4. Technical Bottlenecks
- Technical bottleneck: High memory consumption in worker pods and intermittent cross-region network latency spikes exceeding 1200ms.

Task ID,Task Name,Deliverable,Owner,Priority,Status,Deadline,Dependencies,Notes
TSK-101,Deploy Kafka Ingestion Brokers,Cloud Telemetry Ingestion Pipeline,Alice Chen,High,Completed,2026-08-10,None,Deployed to Kubernetes cluster successfully
TSK-102,Configure RBAC OAuth Gateway,Unified RBAC Security Gateway,Bob Martinez,Critical,In progress,2026-09-28,SecOps Approval,Blocked by security compliance review
TSK-103,Design Executive Chart Components,Real-Time Executive Dashboard,Carol Vance,Medium,In progress,2026-10-15,None,UI mockups approved by stakeholders
TSK-104,Execute Staging Database Migration,Automated Data Warehouse Sync,Unassigned,High,Pending,2026-09-30,Kafka Pipeline,Migration tests failing on staging
TSK-105,Cloud Cost Containment Audit,Budget Optimization,David Kim,High,Pending,2026-10-05,None,Cloud spend exceeded budget by 22%
TSK-106,Automate Multi-Region Failover,Cloud Infrastructure,David Kim,Medium,Pending,2026-11-15,Kubernetes Clusters,Pending secondary cloud provider account setup
TSK-107,Perform Load and Stress Testing,System Reliability,Unassigned,Medium,Pending,2026-11-01,Staging Database Migration,Requires stable staging environment`,
  },
];

// Alias for backwards & multi-page compatibility
export const SAMPLE_DATASETS = SAMPLE_DOCS;
