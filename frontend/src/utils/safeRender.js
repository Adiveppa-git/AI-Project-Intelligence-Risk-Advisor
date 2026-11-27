/**
 * Safe rendering utilities for AI Project Intelligence & Risk Advisor dashboard.
 * Prevents React child object runtime errors such as:
 * "Objects are not valid as a React child (found: object with keys {activity_id, description, reason, evidence})"
 */

/**
 * Safely converts any value (string, number, array, or object) to a printable string.
 * Never returns a JavaScript object child.
 *
 * @param {any} val - The value to render
 * @param {string} [fallback=''] - Optional fallback when value is null/undefined/empty
 * @returns {string} - Clean, printable string
 */
export function renderSafeText(val, fallback = '') {
  if (val == null) return fallback;
  if (typeof val === 'string') return val;
  if (typeof val === 'number' || typeof val === 'boolean') return String(val);
  if (Array.isArray(val)) {
    const rendered = val.map((item) => renderSafeText(item)).filter(Boolean).join(', ');
    return rendered || fallback;
  }
  if (typeof val === 'object') {
    // If it's a DelayedActivity or similar object with {activity_id, description, reason, evidence}
    if (val.description) return String(val.description);
    if (val.title) return String(val.title);
    if (val.name) return String(val.name);
    if (val.activity) return String(val.activity);
    if (val.question) return String(val.question);
    if (val.action) return String(val.action);
    if (val.decision) return String(val.decision);
    if (val.activity_id) return String(val.activity_id);
    if (val.blocker_id) return String(val.blocker_id);
    if (val.snippet) return String(val.snippet);
    if (val.reason) return String(val.reason);
    try {
      return JSON.stringify(val);
    } catch {
      return fallback;
    }
  }
  return String(val);
}

/**
 * Safely extracts the display name for an assignee, owner, or decision-maker.
 * Handles both plain strings and nested objects.
 *
 * @param {any} item - Object containing assignee/owner information
 * @returns {string} - Extracted person name or string
 */
export function getAssigneeName(item) {
  if (!item) return '';
  const person = item.assigned_person ?? item.assignee ?? item.owner ?? item.assigned_owner ?? item.decision_maker;
  if (!person) return '';
  if (typeof person === 'string') return person.trim();
  if (typeof person === 'object') {
    return person.name || person.person || person.assignee || person.owner || JSON.stringify(person);
  }
  return String(person);
}

/**
 * Determines whether an action item or decision is unassigned.
 *
 * @param {any} item - Action item or decision
 * @returns {boolean} - True if unassigned or unknown
 */
export function isItemUnassigned(item) {
  const name = getAssigneeName(item).toLowerCase();
  return !name || name === 'unassigned' || name === 'pending' || name === 'unknown';
}
