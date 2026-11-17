/** Static AST inventory only. Never evaluates archived JavaScript. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { parse } from '../.tools/audit/node_modules/acorn/dist/acorn.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const check = args.includes('--check');
const sourceFlag = args.indexOf('--source');
const sourcePath = sourceFlag < 0
  ? path.join(root, '.tools/reference/advisor/public/engine/advisor.html')
  : path.resolve(args[sourceFlag + 1]);
const source = fs.readFileSync(sourcePath, 'utf8');
const sourceId = 'advisor/public/engine/advisor.html';
const outputDir = path.join(root, 'docs/catalogs');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const properties = n => new Map((n.properties ?? []).filter(p => p.type === 'Property')
  .map(p => [p.key.name ?? p.key.value, p.value]));
const string = n => n?.type === 'Literal' && typeof n.value === 'string' ? n.value : null;
const helpers = new Set(['question', 'M', 'landHousingCheck', 'charityField', 'saleSelect',
  'saleInput', 'select', 'text', 'num', 'area', 'multi', 'heading']);
const rulesPattern = /validat|evaluat|guidance|advice|estimate|temporaryHousing|checkOption|checkNumber|criticalAnswers|fundBankLabel|normalSale|read.*Profile|readProposal|compareFunds|compareSales|compareHeritage|makeBuildingBrief|prepare$/i;
const fields = [], rules = [], scripts = [], unresolved = [], excludedCalls = [];

function mapping(scriptId, context, line) {
  if (scriptId === 'land-preparation-script' || /landHousing/i.test(context))
    return { domain: 'land-preparation', task: 'T20' };
  if (scriptId === 'foreign-investment-script')
    return { domain: 'foreign-investment', task: 'T21' };
  if (scriptId === 'ministry-additions-script') {
    if (/renewal|temporaryHousing/.test(context)) return { domain: 'renewal', task: 'T22' };
    if (/manager/.test(context)) return { domain: 'rental-management', task: 'T23' };
    if (/exchange/.test(context)) return { domain: 'property-exchange', task: 'T23' };
    if (/profile/.test(context)) return { domain: 'professional-profile', task: 'T17' };
    if (/notice|passport/.test(context)) return { domain: 'opportunity-dossier', task: 'T18' };
    return { domain: 'supplementary-services-shared', task: 'T18/T22/T23/T17' };
  }
  if (scriptId === 'vivid-portal-script') return { domain: 'ideas', task: 'T19' };
  if (scriptId === 'ext-script') return /Proposal|proposal|fundingAdvice/.test(context)
    ? { domain: 'proposal', task: 'T19' } : { domain: 'catalog-workspace-guides', task: 'T11/T15/T18' };
  if (/building|assetQuestions|advisoryConfig|sectorAdvisories|sectorGuidance|sectorConditions|criticalAnswers|evaluateCore|buildGuidance/i.test(context))
    return { domain: 'project-specific-advice', task: 'T24' };
  if (/charity/i.test(context) || (!scriptId && line >= 659 && line < 711))
    return { domain: 'charity', task: 'T24' };
  if (/sales|sale[A-Z]/i.test(context)) return { domain: 'sales', task: 'T12' };
  if (/fund/i.test(context)) return { domain: 'funds', task: 'T12' };
  if (/heritage/i.test(context)) return { domain: 'heritage', task: 'T12/T24' };
  if (/method|Method/.test(context)) return { domain: 'route-contract-conditions', task: 'T12' };
  return { domain: 'cross-cutting-source-review', task: 'T01.3' };
}

function contextOf(ancestors) {
  const segments = [];
  for (const n of ancestors) {
    if (n.type === 'VariableDeclarator' && n.id.type === 'Identifier') segments.push(n.id.name);
    else if (n.type === 'Property' && !n.computed) segments.push(String(n.key.name ?? n.key.value));
    else if (n.type === 'FunctionDeclaration' && n.id) segments.push(n.id.name);
  }
  return segments.join('.');
}

let scriptIndex = 0;
for (const match of source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
  const attributes = match[1], code = match[2];
  if (/type\s*=\s*['"](?:application\/ld\+json|application\/json)['"]/.test(attributes)) continue;
  const scriptId = /\bid\s*=\s*["']([^"']+)/.exec(attributes)?.[1] ?? '';
  const offset = match.index + match[0].indexOf('>') + 1;
  const baseLine = source.slice(0, offset).split('\n').length - 1;
  const ast = parse(code, { ecmaVersion: 'latest', sourceType: 'script', locations: true });
  scripts.push({ index: ++scriptIndex, id: scriptId || 'main-script', start_line: baseLine + 1,
    sha256: hash(code), parsed: true });
  const slice = n => n ? code.slice(n.start, n.end) : null;

  function addField(node, ancestors, data) {
    const context = contextOf(ancestors);
    const branchConditions = ancestors.filter(a => a.type === 'IfStatement' || a.type === 'ConditionalExpression')
      .map(a => slice(a.test));
    fields.push({ source: sourceId, script: scriptId || 'main-script',
      line: baseLine + node.loc.start.line, column: node.loc.start.column,
      column_basis: 'script-relative-zero-based', source_start: offset + node.start,
      source_end: offset + node.end, end_line: baseLine + node.loc.end.line, context, ...data,
      enclosing_condition_expressions: [...new Set(branchConditions)],
      enclosing_branches: ancestors.flatMap((a, i) => {
        if (!['IfStatement', 'ConditionalExpression'].includes(a.type)) return [];
        const child = ancestors[i + 1] ?? node;
        return [{ expression: slice(a.test), branch: child === a.consequent ? 'consequent'
          : child === a.alternate ? 'alternate' : 'test' }];
      }),
      definition: slice(node), ...mapping(scriptId, context, baseLine + node.loc.start.line),
      status: 'source-extracted-semantic-review-required' });
  }

  function walk(node, ancestors = []) {
    if (!node || typeof node !== 'object') return;
    const parent = ancestors.at(-1);
    if (node.type === 'CallExpression' && node.callee.type === 'Identifier' && helpers.has(node.callee.name)) {
      const id = string(node.arguments[0]), label = string(node.arguments[1]);
      // num is also used as a one-argument numeric converter in unrelated scopes.
      if (node.callee.name === 'num' && node.arguments.length < 2) {
        excludedCalls.push({ line: baseLine + node.loc.start.line, context: contextOf(ancestors),
          definition: slice(node), reason: 'numeric-conversion-not-field-helper' });
      } else if (id !== null && node.arguments[1]) {
        const helper = node.callee.name;
        let when = null;
        if (helper === 'question') when = slice(node.arguments[4]);
        if (helper === 'M') when = slice(node.arguments[5]);
        for (const arg of node.arguments) if (arg.type === 'ObjectExpression') {
          const props = properties(arg); if (props.has('when')) when = slice(props.get('when'));
        }
        addField(node, ancestors, { kind: helper === 'heading' ? 'section-heading' : 'helper-field',
          field_id: id, label, label_expression: slice(node.arguments[1]), helper,
          control_expression: helper === 'M' ? slice(node.arguments[2]) : helper,
          visibility_expression: when, arguments: node.arguments.map(slice) });
      } else unresolved.push({ source: sourceId, script: scriptId || 'main-script',
        line: baseLine + node.loc.start.line, context: contextOf(ancestors), helper: node.callee.name,
        id_expression: slice(node.arguments[0]), label_expression: slice(node.arguments[1]),
        definition: slice(node), reason: 'nonliteral-helper-arguments' });
    }
    if (node.type === 'ObjectExpression') {
      const props = properties(node), id = string(props.get('id'));
      const label = string(props.get('label')), serviceQuestion = string(props.get('question'));
      if (id && (label || serviceQuestion)) {
        addField(node, ancestors, { kind: label ? 'object-field' : 'service-question',
          field_id: id, label: label ?? serviceQuestion, helper: null,
          control_expression: slice(props.get('type')), visibility_expression: slice(props.get('when')),
          service_name: string(props.get('name')), definition_properties: [...props.keys()] });
      }
    }
    // International applicant schemas store field descriptors as tuples under .fields.
    if (node.type === 'ArrayExpression' && parent?.type === 'ArrayExpression') {
      const property = ancestors.at(-2);
      if (property?.type === 'Property' && (property.key.name ?? property.key.value) === 'fields') {
        const id = string(node.elements[0]), label = string(node.elements[1]);
        if (id && label) addField(node, ancestors, { kind: 'tuple-field', field_id: id, label,
          helper: null, control_expression: slice(node.elements[2]), visibility_expression: null });
      }
    }
    if (['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(node.type)) {
      const name = node.id?.name ?? (parent?.type === 'VariableDeclarator' ? parent.id.name : null)
        ?? (parent?.type === 'Property' ? String(parent.key.name ?? parent.key.value) : null);
      if (name && rulesPattern.test(name)) {
        const context = contextOf(ancestors.concat(node.type === 'FunctionDeclaration' ? [node] : []));
        const conditions = [], returns = [];
        function inspect(n) {
          if (!n || typeof n !== 'object') return;
          if (n !== node && ['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'].includes(n.type)) return;
          if (n.type === 'IfStatement' || n.type === 'ConditionalExpression') conditions.push(slice(n.test));
          if (n.type === 'ReturnStatement') returns.push(slice(n.argument));
          for (const v of Object.values(n)) if (Array.isArray(v)) v.forEach(inspect); else if (v?.type) inspect(v);
        }
        inspect(node);
        rules.push({ name, source: sourceId, script: scriptId || 'main-script',
          line: baseLine + node.loc.start.line, end_line: baseLine + node.loc.end.line, context,
          source_start: offset + node.start, source_end: offset + node.end,
          parameters: node.params.map(slice), conditions: [...new Set(conditions)], returns,
          definition: slice(node), ...mapping(scriptId, context, baseLine + node.loc.start.line),
          status: 'rule-source-extracted-not-runtime-verified' });
      }
    }
    for (const [key, value] of Object.entries(node)) {
      if (['loc', 'start', 'end'].includes(key)) continue;
      if (Array.isArray(value)) {
        for (const child of value) if (child?.type) walk(child, [...ancestors, node]);
      } else if (value?.type) walk(value, [...ancestors, node]);
    }
  }
  walk(ast);
}

fields.sort((a, b) => a.line - b.line || a.column - b.column);
fields.forEach((row, index) => row.id = `DF-${String(index + 1).padStart(4, '0')}`);
rules.forEach((row, index) => row.id = `DR-${String(index + 1).padStart(3, '0')}`);
const canonicalText = fs.readFileSync(path.join(root, '.tools/reference/advisor/src/data/fields.ts'), 'utf8');
const canonicalIds = new Set([...canonicalText.matchAll(/id: "([^"]+)", label: "[^"]+"/g)].map(m => m[1]));
const actualFields = fields.filter(row => row.kind !== 'section-heading');
const fieldIds = [...new Set(actualFields.map(row => row.field_id))].sort();
const missingIds = fieldIds.filter(id => !canonicalIds.has(id));
const countBy = (rows, key) => rows.reduce((out, row) => (out[row[key]] = (out[row[key]] ?? 0) + 1, out), {});
const summary = {
  source: sourceId, source_sha256: hash(source), parser: 'acorn@8.15.0',
  method: 'static AST extraction; no execution of archived code', scripts,
  parsed_scripts: scripts.length, field_definition_occurrences: fields.length,
  nonheading_field_occurrences: actualFields.length, distinct_field_id_strings: fieldIds.length,
  field_kinds: countBy(fields, 'kind'), fields_by_domain: countBy(actualFields, 'domain'),
  canonical_field_id_count: canonicalIds.size, id_strings_absent_from_canonical_fields: missingIds,
  canonical_source: 'advisor/src/data/fields.ts', canonical_source_sha256: hash(canonicalText),
  dynamic_label_occurrences: fields.filter(row => row.label === null).length,
  rule_function_occurrences: rules.length, rules_by_domain: countBy(rules, 'domain'),
  unresolved_helper_calls: unresolved.length, excluded_numeric_conversion_calls: excludedCalls.length,
  limitations: [
    'Occurrences are not unique business fields: shared IDs can have different meanings in different flows.',
    'ID overlap does not establish semantic equivalence; absence does not establish missing UI because LegacyTool runs HTML.',
    'Static tuple/helper/object extraction is bounded to recognized source shapes; arbitrary generated HTML controls are not exhaustively enumerated.',
    'Visibility expressions and ancestor tests are source expressions, not an exhaustive reachable-state analysis.',
    'Module/task routing is a proposed heuristic mapping to be reviewed before implementation.',
    'Function inventory is selected by rule-related names; it is not proof that all business rules have been identified.',
    'No source behavior, financial claim, legal rule or external reference has been independently validated.'
  ]
};
if (scripts.length < 2 || !fields.length || !rules.length) throw new Error('Incomplete parsing');
if (new Set(fields.map(row => row.id)).size !== fields.length) throw new Error('Duplicate catalog IDs');
for (const row of [...fields, ...rules]) {
  if (source.slice(row.source_start, row.source_end) !== row.definition)
    throw new Error(`Source span mismatch: ${row.id}`);
  if (source.slice(0, row.source_start).split('\n').length !== row.line)
    throw new Error(`Source line mismatch: ${row.id}`);
}
for (const id of ['households', 'gis', 'deposit', 'tenor']) {
  if (!fieldIds.includes(id)) throw new Error(`Expected dynamic field missing: ${id}`);
}
const generated = { 'dynamic-fields.json': fields, 'dynamic-rules.json': rules,
  'dynamic-unresolved.json': { unresolved_helper_calls: unresolved, excluded_numeric_conversion_calls: excludedCalls },
  'dynamic-summary.json': summary };
fs.mkdirSync(outputDir, { recursive: true });
for (const [name, value] of Object.entries(generated)) {
  const content = JSON.stringify(value, null, 2) + '\n';
  const destination = path.join(outputDir, name);
  if (check) {
    if (!fs.existsSync(destination) || fs.readFileSync(destination, 'utf8') !== content)
      throw new Error(`Catalog drift: ${name}`);
  } else fs.writeFileSync(destination, content);
}
console.log(JSON.stringify({ mode: check ? 'check' : 'build', parsed_scripts: scripts.length,
  field_occurrences: fields.length, distinct_field_ids: fieldIds.length, rules: rules.length,
  unresolved_helper_calls: unresolved.length, status: 'passed' }));
