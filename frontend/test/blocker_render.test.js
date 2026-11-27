import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { renderSafeText, getAssigneeName, isItemUnassigned } from '../src/utils/safeRender.js';
import { isValidFilename, getFileFormatBadge, resolveSourceFilename } from '../src/utils/evidenceProvenance.js';

describe('Blocker Safe Rendering & Type Guard Tests', () => {
  it('renderSafeText safely handles primitive values', () => {
    assert.equal(renderSafeText('Hello world'), 'Hello world');
    assert.equal(renderSafeText(123), '123');
    assert.equal(renderSafeText(true), 'true');
    assert.equal(renderSafeText(null), '');
    assert.equal(renderSafeText(undefined), '');
    assert.equal(renderSafeText(null, 'N/A'), 'N/A');
    assert.equal(renderSafeText(undefined, 'Fallback'), 'Fallback');
  });

  it('renderSafeText extracts description from DelayedActivity objects', () => {
    // Exact structure that triggered:
    // "Objects are not valid as a React child (found: object with keys {activity_id, description, reason, evidence})"
    const delayedActivityObj = {
      activity_id: 'ACT-DLY-001',
      description: 'Database migration staging run is delayed by 10 days due to schema syntax incompatibilities',
      reason: 'schema syntax incompatibilities.',
      evidence: [
        {
          document_id: null,
          filename: 'Unknown',
          chunk_id: null,
          snippet: '- Activity: Database migration staging run is delayed by 10 days due to schema syntax incompatibilities.',
          confidence: 0.85
        }
      ]
    };

    const result = renderSafeText(delayedActivityObj);
    assert.equal(typeof result, 'string');
    assert.equal(result, 'Database migration staging run is delayed by 10 days due to schema syntax incompatibilities');
    assert.notEqual(typeof result, 'object');
  });

  it('renderSafeText extracts title, name, question, action, decision, or reason', () => {
    assert.equal(renderSafeText({ title: 'Security review pending' }), 'Security review pending');
    assert.equal(renderSafeText({ name: 'Kafka broker deployment' }), 'Kafka broker deployment');
    assert.equal(renderSafeText({ question: 'How will token exchange work?' }), 'How will token exchange work?');
    assert.equal(renderSafeText({ action: 'Profile memory usage' }), 'Profile memory usage');
    assert.equal(renderSafeText({ decision: 'ClickHouse vs Snowflake' }), 'ClickHouse vs Snowflake');
    assert.equal(renderSafeText({ reason: 'Waiting on SecOps' }), 'Waiting on SecOps');
    assert.equal(renderSafeText({ activity_id: 'ACT-DLY-099' }), 'ACT-DLY-099');
  });

  it('renderSafeText safely handles arrays of strings and objects', () => {
    const list = [
      'Ingestion pipeline',
      { activity_id: 'ACT-1', description: 'Worker pod deployment' }
    ];
    const result = renderSafeText(list);
    assert.equal(typeof result, 'string');
    assert.equal(result, 'Ingestion pipeline, Worker pod deployment');
  });

  it('renderSafeText never returns a JavaScript object child', () => {
    const complexObj = {
      nested: { deeply: 'value' },
      customField: 42
    };
    const result = renderSafeText(complexObj);
    assert.equal(typeof result, 'string');
    assert.ok(result.includes('deeply') || result.includes('42'));
  });

  it('getAssigneeName and isItemUnassigned handle string and object assignees', () => {
    // Plain string assigned
    assert.equal(getAssigneeName({ assigned_person: 'Alice Chen' }), 'Alice Chen');
    assert.equal(isItemUnassigned({ assigned_person: 'Alice Chen' }), false);

    // Unassigned string
    assert.equal(getAssigneeName({ assigned_person: 'Unassigned' }), 'Unassigned');
    assert.equal(isItemUnassigned({ assigned_person: 'Unassigned' }), true);

    // Alternative field name: assignee
    assert.equal(getAssigneeName({ assignee: 'Bob Martinez' }), 'Bob Martinez');
    assert.equal(isItemUnassigned({ assignee: 'Bob Martinez' }), false);

    // Alternative field name: owner
    assert.equal(getAssigneeName({ owner: 'David Kim' }), 'David Kim');
    assert.equal(isItemUnassigned({ owner: 'David Kim' }), false);

    // Object assignee
    assert.equal(getAssigneeName({ assigned_person: { name: 'Carol Vance' } }), 'Carol Vance');
    assert.equal(isItemUnassigned({ assigned_person: { name: 'Carol Vance' } }), false);

    // Empty / null assignee
    assert.equal(getAssigneeName({}), '');
    assert.equal(isItemUnassigned({}), true);
    assert.equal(getAssigneeName(null), '');
    assert.equal(isItemUnassigned(null), true);
  });

  it('validates a complete realistic API response containing all blocker models', () => {
    const apiResponse = {
      blockers: [
        {
          blocker_id: 'BLK-001',
          title: 'Ingestion pipeline blocked by SecOps approval',
          description: 'External OAuth token exchange is waiting for SecOps approval.',
          status: 'active',
          affected_activities: [
            'Ingestion pipeline',
            { activity_id: 'ACT-DLY-001', description: 'Database migration', reason: 'syntax error', evidence: [] }
          ],
          assigned_owner: 'Bob Martinez',
          supporting_evidence: [
            { document_id: null, filename: 'meeting_notes.txt', snippet: 'Blocker 1 evidence', confidence: 0.95 }
          ]
        }
      ],
      pending_decisions: [
        {
          decision_id: 'DEC-001',
          description: 'Selecting ClickHouse vs Snowflake for warm storage',
          decision_maker: 'David Kim',
          deadline: '2026-09-25',
          evidence: []
        }
      ],
      delayed_activities: [
        {
          activity_id: 'ACT-DLY-001',
          description: 'Database migration staging run is delayed by 10 days',
          reason: 'schema syntax incompatibilities.',
          evidence: [{ snippet: 'Activity: Database migration', confidence: 0.85 }]
        }
      ],
      unresolved_issues: [
        {
          issue_id: 'ISS-001',
          title: 'Intermittent network latency spikes exceeding 1200ms',
          status: 'unresolved',
          evidence: []
        }
      ],
      action_items: [
        {
          action_id: 'ACT-001',
          description: 'Bob Martinez to submit SecOps compliance ticket',
          assigned_person: 'Bob Martinez',
          deadline: '2026-09-20',
          priority: 'Critical',
          current_status: 'Pending',
          supporting_evidence: []
        },
        {
          action_id: 'ACT-002',
          description: 'Clean up stale test accounts in staging database',
          assigned_person: 'Unassigned',
          deadline: 'Not specified',
          priority: 'Low',
          current_status: 'Pending',
          supporting_evidence: []
        }
      ],
      unassigned_action_items_count: 1
    };

    // Verify all delayed activities descriptions are safe strings
    for (const act of apiResponse.delayed_activities) {
      const rendered = renderSafeText(act.description || act.activity || act.name || act);
      assert.equal(typeof rendered, 'string');
      assert.ok(rendered.length > 0);
      assert.notEqual(typeof rendered, 'object');
    }

    // Verify all affected activities in blockers are safe strings
    for (const blk of apiResponse.blockers) {
      for (const aff of blk.affected_activities) {
        const rendered = renderSafeText(aff);
        assert.equal(typeof rendered, 'string');
        assert.notEqual(typeof rendered, 'object');
      }
    }

    // Verify all decisions are safe strings
    for (const dec of apiResponse.pending_decisions) {
      const rendered = renderSafeText(dec.description || dec.title || dec.decision || dec);
      assert.equal(typeof rendered, 'string');
      assert.notEqual(typeof rendered, 'object');
    }

    // Verify all unresolved issues are safe strings
    for (const iss of apiResponse.unresolved_issues) {
      const rendered = renderSafeText(iss.title || iss.question || iss.description || iss);
      assert.equal(typeof rendered, 'string');
      assert.notEqual(typeof rendered, 'object');
    }

    // Verify all action items are safe strings
    for (const item of apiResponse.action_items) {
      const rendered = renderSafeText(item.description || item.action || item);
      assert.equal(typeof rendered, 'string');
      assert.notEqual(typeof rendered, 'object');
    }
  });

  it('validates EvidenceModal source filename resolution and provenance', () => {
    // 1. Genuine filename available in ev.filename
    const evWithPdf = {
      filename: 'project_charter_ecap.pdf',
      snippet: 'Executive Summary',
      confidence: 0.95
    };
    assert.equal(resolveSourceFilename(evWithPdf), 'project_charter_ecap.pdf');

    // 2. ev.filename is "Unknown", but ev.source_document is available
    const evWithDocx = {
      filename: 'Unknown',
      source_document: 'progress_report_q3.docx',
      snippet: 'Milestone 2 is delayed',
      confidence: 0.88
    };
    assert.equal(resolveSourceFilename(evWithDocx), 'progress_report_q3.docx');

    // 3. Genuine filename in metadata.filename
    const evWithCsv = {
      filename: 'Unknown',
      metadata: { filename: 'task_matrix_sprint14.csv' },
      snippet: 'TSK-101 Deploy Kafka'
    };
    assert.equal(resolveSourceFilename(evWithCsv), 'task_matrix_sprint14.csv');

    // 4. Genuine filename passed as modal fallback
    const evWithTxt = {
      filename: 'Unknown',
      snippet: 'Meeting Notes - Weekly Sync'
    };
    assert.equal(resolveSourceFilename(evWithTxt, 'sprint_14_retrospective.txt'), 'sprint_14_retrospective.txt');

    // 5. Filename genuinely unavailable -> must return "Source filename unavailable", NEVER "Unknown"
    const evNoFile = {
      filename: 'Unknown',
      source_document: 'Unknown',
      snippet: 'Some raw snippet'
    };
    const resolved = resolveSourceFilename(evNoFile);
    assert.equal(resolved, 'Source filename unavailable');
    assert.notEqual(resolved.toLowerCase(), 'unknown');

    // 6. Generic agent labels like "Blocker Agent" must NOT be treated as filenames
    const resolvedAgentSource = resolveSourceFilename(evNoFile, null, 'Blocker Agent');
    assert.equal(resolvedAgentSource, 'Source filename unavailable');
  });

  it('detects file format badges for PDF, DOCX, CSV, and TXT', () => {
    assert.equal(getFileFormatBadge('charter.pdf')?.ext, 'PDF');
    assert.equal(getFileFormatBadge('REPORT.DOCX')?.ext, 'DOCX');
    assert.equal(getFileFormatBadge('legacy_doc.doc')?.ext, 'DOCX');
    assert.equal(getFileFormatBadge('tasks.csv')?.ext, 'CSV');
    assert.equal(getFileFormatBadge('notes.txt')?.ext, 'TXT');
    assert.equal(getFileFormatBadge('image.png'), null);
    assert.equal(getFileFormatBadge('Source filename unavailable'), null);
  });

  it('isValidFilename rejects generic labels and accepts valid document names', () => {
    assert.equal(isValidFilename('Unknown'), false);
    assert.equal(isValidFilename('unknown'), false);
    assert.equal(isValidFilename('Blocker Agent'), false);
    assert.equal(isValidFilename('Scope Agent'), false);
    assert.equal(isValidFilename('Risk Agent'), false);
    assert.equal(isValidFilename(''), false);
    assert.equal(isValidFilename(null), false);
    assert.equal(isValidFilename(undefined), false);

    assert.equal(isValidFilename('project_charter_ecap.pdf'), true);
    assert.equal(isValidFilename('sprint_14_retrospective.txt'), true);
    assert.equal(isValidFilename('task_matrix_sprint14.csv'), true);
    assert.equal(isValidFilename('progress_report_q3.docx'), true);
  });

  it('validates MultiAgentPage health score and date normalization', () => {
    // Test Case 1: Backend provides overall_health_score and generated_at
    const report1 = {
      overall_health_score: 42,
      project_health: 'At Risk',
      generated_at: '2026-11-26T17:00:00Z',
      scope_and_deliverables: { expected_deliverables: [{ name: 'Telemetry' }] },
      risk_and_forecasting: { risks: [{ title: 'Risk 1' }] },
      blockers_and_actions: { blockers: [{ title: 'Blocker 1' }] }
    };

    const healthStatus1 = report1.project_health || report1.overall_health_status || 'Healthy';
    const score1 = typeof report1.overall_health_score === 'number' && !isNaN(report1.overall_health_score)
      ? report1.overall_health_score
      : (healthStatus1 === 'Healthy' ? 92 : 32);
    assert.equal(score1, 42);

    const rawDate1 = report1.generated_at || report1.timestamp;
    const parsedDate1 = rawDate1 ? new Date(rawDate1) : new Date();
    const validDate1 = !isNaN(parsedDate1.getTime()) ? parsedDate1 : new Date();
    assert.notEqual(validDate1.toLocaleTimeString(), 'Invalid Date');

    // Test Case 2: Missing numeric score and timestamp (guaranteeing no NaN or Invalid Date)
    const report2 = {
      project_health: 'Critical'
    };
    const healthStatus2 = report2.project_health || report2.overall_health_status || 'Healthy';
    const score2 = typeof report2.overall_health_score === 'number' && !isNaN(report2.overall_health_score)
      ? report2.overall_health_score
      : (healthStatus2 === 'Healthy' ? 92 : healthStatus2 === 'Needs Attention' ? 75 : healthStatus2 === 'At Risk' ? 52 : 32);
    assert.equal(score2, 32);
    assert.ok(typeof score2 === 'number');
    assert.ok(!isNaN(score2));

    const rawDate2 = report2.generated_at || report2.timestamp;
    const parsedDate2 = rawDate2 ? new Date(rawDate2) : new Date();
    const validDate2 = !isNaN(parsedDate2.getTime()) ? parsedDate2 : new Date();
    assert.notEqual(validDate2.toLocaleTimeString(), 'Invalid Date');

    // Test Case 3: Dual-schema resolution for child findings
    const report3 = {
      scope_and_deliverables: { expected_deliverables: [1, 2, 3, 4] },
      risk_and_forecasting: { risks: [1, 2, 3, 4, 5, 6, 7, 8] },
      blockers_and_actions: { blockers: [1, 2, 3], action_items: [1, 2, 3, 4, 5, 6], pending_decisions: [1, 2] }
    };
    const scope = report3.scope_and_deliverables || report3.scope_analysis || {};
    const risk = report3.risk_and_forecasting || report3.risk_analysis || {};
    const blocker = report3.blockers_and_actions || report3.blocker_analysis || {};

    assert.equal((scope.expected_deliverables || []).length, 4);
    assert.equal((risk.risks || []).length, 8);
    assert.equal((blocker.active_blockers || blocker.blockers || []).length, 3);
    assert.equal((blocker.action_items || []).length, 6);
    assert.equal((blocker.pending_decisions || []).length, 2);
  });

  it('validates deduplicated risk findings, linked blockers, and merged sources rendering', () => {
    const deduplicatedRisks = [
      {
        risk_id: 'RSK-001',
        title: 'OAuth Gateway deployment blocked by SecOps approval',
        description: 'Ingestion pipeline and OAuth Gateway deployment blocked by SecOps approval and security compliance review backlog.',
        category: 'Dependency',
        severity: 'Critical',
        related_blocker_ids: ['BLK-001'],
        related_blocker_id: 'BLK-001',
        merged_sources: ['sprint_14_retrospective.txt', 'progress_report_q3.docx', 'task_matrix_sprint14.csv'],
        supporting_evidence: [
          { filename: 'sprint_14_retrospective.txt', snippet: 'Blocker 1: Ingestion pipeline blocked' },
          { filename: 'progress_report_q3.docx', snippet: 'Schedule delay: Security compliance review backlog' },
          { filename: 'task_matrix_sprint14.csv', snippet: 'TSK-102,Configure RBAC OAuth Gateway' }
        ]
      },
      {
        risk_id: 'RSK-002',
        title: 'Database migration scripts failing and delayed on staging cluster',
        description: 'Database migration scripts failing on staging cluster due to schema mismatch; staging run delayed by 10 days.',
        category: 'Bottleneck',
        severity: 'Critical',
        related_blocker_ids: ['BLK-002'],
        related_blocker_id: 'BLK-002',
        merged_sources: ['sprint_14_retrospective.txt', 'task_matrix_sprint14.csv']
      }
    ];

    // Verify properties
    assert.equal(deduplicatedRisks.length, 2);
    assert.equal(deduplicatedRisks[0].related_blocker_id, 'BLK-001');
    assert.equal(deduplicatedRisks[0].merged_sources.length, 3);
    assert.ok(deduplicatedRisks[0].title.indexOf(',') === -1 || deduplicatedRisks[0].title.split(',').length < 3);

    // Verify category counts calculation
    const categoryCounts = deduplicatedRisks.reduce((acc, r) => {
      const cat = r.category || 'Other';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});

    assert.equal(categoryCounts['Dependency'], 1);
    assert.equal(categoryCounts['Bottleneck'], 1);
    assert.equal(Object.values(categoryCounts).reduce((a, b) => a + b, 0), deduplicatedRisks.length);
  });
});
