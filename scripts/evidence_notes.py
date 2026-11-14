"""Render the scientific interpretation kept alongside each dataset."""
from pathlib import Path


def render_evidence_summary(record):
    summary = record['evidence_summary']
    lines = ['# ' + record['descriptor']['metadata']['title'], '']
    for key, label in [('question', 'Question'), ('finding', 'What the study found'),
                       ('interpretation', 'How to use the evidence'),
                       ('evidence_type', 'How the evidence was obtained'),
                       ('dataset_role', 'What this dataset contributes')]:
        lines.extend(['## ' + label, '', summary[key], ''])
    lines.extend(['## Limits and interpretation', ''])
    lines.extend('- ' + item for item in summary['limitations'])
    lines.extend(['', '## Sources for these statements', ''])
    for source in summary['sources']:
        lines.extend(['- [' + source['title'] + '](' + source['url'] + '). '
                      + source['location'] + '. ' + source['supports']])
    lines.extend(['', 'These notes describe scientific findings and their potential use. '
                  'They do not establish that a particular policy was adopted because of the study.', '',
                  '[Full provenance, matching evidence and preparation checks](review-context.json).', ''])
    return '\n'.join(lines)


def write_evidence_summary(folder: Path, record: dict):
    if 'evidence_summary' in record:
        (folder / 'evidence-summary.md').write_text(render_evidence_summary(record),
                                                   encoding='utf-8', newline='\n')


def pilot_evidence_context(record):
    context = dict(record['review_context'])
    if 'evidence_summary' in record:
        context['evidence_summary'] = record['evidence_summary']
        context['metadata_history'] = record.get('metadata_history', [])
    return context
