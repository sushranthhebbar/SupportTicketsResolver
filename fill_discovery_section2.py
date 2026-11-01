from docx import Document
from docx.shared import Inches


path = r"docs/reference/02_Stage_Workbooks/Stage_1_Discovery_Workbook.docx"
doc = Document(path)
table = doc.tables[5]
table.autofit = False
column_widths = [Inches(1.8), Inches(1.45), Inches(2.1), Inches(1.35)]
for column, width in zip(table.columns, column_widths):
    column.width = width
    for cell in column.cells:
        cell.width = width


def set_lines(cell, lines):
    paragraph = cell.paragraphs[0]
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)
    for index, line in enumerate(lines):
        if index:
            paragraph.add_run().add_break()
        paragraph.add_run(line)


entries = [
    (
        ["500"],
        [
            "Source: evaluation/data/development_tickets.json. Count the top-level ticket records; there are 500 unique ticket_id values, from DEV-0001 through DEV-0500."
        ],
    ),
    (
        [
            "email: 42.4%",
            "chat: 31.0%",
            "documentation comments: 15.6%",
            "forum: 11.0%",
        ],
        [
            "Group all records by channel and divide each group by 500.",
            "email: 212/500",
            "chat: 155/500",
            "docs_comment: 78/500",
            "forum: 55/500",
        ],
    ),
    (
        [
            "Account access: 4.4%",
            "API key issue: 3.6%",
            "API usage question: 4.8%",
            "Authentication failure: 4.0%",
            "Billing query: 4.8%",
            "Compliance request: 5.2%",
            "Configuration help: 3.4%",
            "Data export: 5.8%",
            "Data residency: 5.8%",
            "Database issue: 5.2%",
            "Deployment failure: 5.4%",
            "Feature request: 4.0%",
            "Integration help: 4.2%",
            "Onboarding: 4.4%",
            "Performance degradation: 4.6%",
            "Quota or overage: 4.6%",
            "Rate limit: 2.6%",
            "Rollback request: 5.6%",
            "Security incident: 5.2%",
            "SSO configuration: 5.2%",
            "Unclear request: 3.0%",
            "Webhook issue: 4.2%",
        ],
        [
            "Group by labels.intent and divide each group by 500. Counts by category in the same order as the figure:",
            "22, 18, 24, 20, 24, 26, 17, 29, 29, 26, 27",
            "20, 21, 22, 23, 23, 13, 28, 26, 26, 15, 21",
        ],
    ),
    (
        ["medium: 45.2%", "high: 29.2%", "low: 25.6%"],
        [
            "Group by labels.urgency and divide each group by 500.",
            "medium: 226/500",
            "high: 146/500",
            "low: 128/500",
        ],
    ),
    (
        ["43.8%"],
        [
            "history.first_contact_resolution is true for 219 tickets; divide 219 by all 500 tickets."
        ],
    ),
    (
        ["2.97 out of 5"],
        [
            "Arithmetic mean of history.csat_rating across all 500 tickets, rounded to two decimal places."
        ],
    ),
    (
        [
            "\u201cHow do I revert to an earlier revision? The release we put out this morning is causing errors and I would rather roll back than try to fix forward.\u201d",
            "2.8% of tickets",
        ],
        [
            "Group body text after trimming, lowercasing, and collapsing whitespace. The top phrase appears in 14/500 tickets. Matching ticket IDs:",
            "DEV-0009, DEV-0040, DEV-0042, DEV-0122, DEV-0127, DEV-0157, DEV-0163",
            "DEV-0263, DEV-0315, DEV-0339, DEV-0345, DEV-0386, DEV-0423, DEV-0473",
        ],
    ),
    (
        ["71.4%"],
        [
            "labels.answerable_from_docs is true for 357 tickets; divide 357 by all 500 tickets."
        ],
    ),
    (
        [
            "Marked non-fluent: 24.0%",
            "First-contact resolution: 45.8%",
            "Average satisfaction: 3.04/5",
            "Escalated: 54.2%",
            "Repeat contact: 19.2%",
            "Mean resolution time: 466.1 minutes",
        ],
        [
            "Filter language_fluency = non_fluent: 120/500 tickets. Within the 120-ticket segment:",
            "history.first_contact_resolution true: 55/120",
            "history.csat_rating mean: 3.04/5",
            "history.escalated true: 65/120",
            "history.repeat_contact true: 23/120",
            "history.resolution_time_minutes mean: 466.1",
        ],
    ),
    (
        [
            "Business",
            "First-contact resolution: 48.2%",
            "Satisfaction: 2.91/5",
            "Escalated: 51.8%",
            "Repeat contact: 23.2%",
            "Mean resolution time: 358.8 minutes",
            "",
            "Enterprise",
            "First-contact resolution: 37.3%",
            "Satisfaction: 3.05/5",
            "Escalated: 62.7%",
            "Repeat contact: 24.1%",
            "Mean resolution time: 483.7 minutes",
            "",
            "Standard",
            "First-contact resolution: 43.1%",
            "Satisfaction: 2.98/5",
            "Escalated: 56.9%",
            "Repeat contact: 19.8%",
            "Mean resolution time: 442.1 minutes",
        ],
        [
            "Group by customer_tier: business n=164; enterprise n=83; standard n=253.",
            "For each tier, calculate rates from history.first_contact_resolution, history.escalated, and history.repeat_contact. Average history.csat_rating and history.resolution_time_minutes."
        ],
    ),
    (
        ["21.6%"],
        [
            "history.repeat_contact is true for 108 tickets; divide 108 by all 500 tickets."
        ],
    ),
]

for row, (figure, source) in zip(table.rows[1:12], entries):
    set_lines(row.cells[1], figure)
    set_lines(row.cells[2], source)
    set_lines(row.cells[3], [])

doc.save(path)
