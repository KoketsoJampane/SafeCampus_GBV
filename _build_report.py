from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
TEMPLATE = Path(r"C:\Users\Admin\Downloads\NPRJ740_Final_Project_Report_Template (2).docx")
OUTPUT = ROOT / "SafeCampus_GBV_Final_Project_Report.docx"
DATE = "6 November 2026"


def shade(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def set_cell_text(cell, text, bold=False, color=None, size=9):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(2)
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True, color="FFFFFF", size=font_size)
        shade(table.rows[0].cells[i], "17365D")
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, size=font_size)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_para(doc, text="", style=None, bold_prefix=None):
    p = doc.add_paragraph(style=style)
    if bold_prefix and text.startswith(bold_prefix):
        p.add_run(bold_prefix).bold = True
        p.add_run(text[len(bold_prefix):])
    else:
        p.add_run(text)
    return p


def add_bullets(doc, items):
    for item in items:
        add_para(doc, item, "List Bullet")


def add_numbered(doc, items):
    for item in items:
        add_para(doc, item, "List Number")


def add_mermaid(doc, title, source, note=None):
    doc.add_heading(title, level=3)
    if note:
        add_para(doc, note)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(9)
    p.paragraph_format.left_indent = Inches(0.12)
    p.paragraph_format.right_indent = Inches(0.12)
    p.paragraph_format.keep_together = True
    run = p.add_run(source.strip())
    run.font.name = "Consolas"
    run.font.size = Pt(7)
    run.font.color.rgb = RGBColor(35, 54, 80)


def heading(doc, text, level=1):
    doc.add_heading(text, level=level)


def reset_document(doc):
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)
    styles = doc.styles
    for style_name in ("Normal", "Body Text"):
        if style_name in styles:
            styles[style_name].font.name = "Arial"
            styles[style_name].font.size = Pt(10)
            styles[style_name].paragraph_format.space_after = Pt(5)
    styles["Heading 1"].font.name = "Arial"
    styles["Heading 1"].font.color.rgb = RGBColor(23, 54, 93)
    styles["Heading 1"].font.size = Pt(16)
    styles["Heading 1"].font.bold = True
    styles["Heading 2"].font.name = "Arial"
    styles["Heading 2"].font.color.rgb = RGBColor(31, 78, 121)
    styles["Heading 2"].font.size = Pt(12)
    styles["Heading 2"].font.bold = True
    styles["Heading 3"].font.name = "Arial"
    styles["Heading 3"].font.size = Pt(10.5)
    styles["Heading 3"].font.bold = True


CONTEXT = r"""
graph TD
    Visitor[Visitor] -->|Register, sign in, reset password, contact| App[SafeCampus GBV System]
    Student[Student] <-->|Reports, evidence, profile, chats, resources| App
    Staff[Staff Member] <-->|Reports, profile, support| App
    Counselor[Counselor] <-->|Assigned cases, case notes, support, recordings| App
    Security[Security Officer] <-->|Incident alerts, case status, notes| App
    Admin[Administrator] <-->|User verification, assignments, resources, reports| App
    App <-->|Accounts, reports, support, messages, resources| DB[(MySQL Database)]
    App <-->|Evidence, qualifications, profile images, session videos| Files[Local Media Storage]
    App -->|Panic SMS| BulkSMS[BulkSMS API]
    App -->|Registration and notification emails| Email[EmailJS and Django Email]
    Student -. Quick Exit browser redirect .-> Weather[Google Weather Search]
"""

USE_CASE = r"""
flowchart LR
    Visitor[Visitor]
    Student[Student]
    Staff[Staff]
    Counselor[Counselor]
    Security[Security Officer]
    Admin[Administrator]
    subgraph SafeCampus["SafeCampus GBV System"]
        Auth((Register / Sign in / Reset password))
        Profile((Manage profile))
        Qual((Upload qualification))
        Report((Submit report))
        Evidence((Attach evidence))
        Track((Track own reports))
        Chat((Start / reply to support chat))
        Resources((Browse resources))
        Panic((Trigger Quick Exit))
        Cases((Review cases))
        Update((Update status / add notes))
        Recording((Upload session recording))
        MySessions((View session recordings))
        Verify((Verify user))
        Assign((Assign report / set priority))
        Manage((Manage users and resources))
        Audit((View activity log))
    end
    Visitor --- Auth
    Student --- Profile
    Student --- Report
    Report -. optional .-> Evidence
    Student --- Track
    Student --- Chat
    Student --- Resources
    Student --- Panic
    Student --- MySessions
    Staff --- Profile
    Staff --- Qual
    Staff --- Report
    Staff --- Chat
    Counselor --- Qual
    Counselor --- Cases
    Counselor --- Update
    Counselor --- Chat
    Counselor --- Recording
    Security --- Cases
    Security --- Update
    Security --- Panic
    Admin --- Verify
    Admin --- Assign
    Admin --- Manage
    Admin --- Audit
    Admin --- Cases
"""

ARCHITECTURE = r"""
flowchart TB
    Browser[Web browser: Django templates, HTML, CSS, JavaScript]
    Django[Django monolithic web application]
    Auth[Django authentication and session middleware]
    Views[Dashboard views and role-specific workflows]
    Models[Django ORM models]
    Mail[EmailJS registration template and Django email utilities]
    Sms[BulkSMS REST API]
    DB[(MySQL)]
    Media[Local media directory]
    Geo[Browser Geolocation API]
    Weather[Google Weather Search]
    Browser -->|HTTP/HTTPS| Django
    Django --> Auth
    Django --> Views
    Views --> Models
    Models <-->|ORM queries| DB
    Views -->|Evidence and recording files| Media
    Browser -->|Welcome message template request| Mail
    Views -->|Notifications| Mail
    Views -->|Panic alert HTTP POST| Sms
    Browser -->|Location permission| Geo
    Geo --> Browser
    Browser -. Quick Exit redirect .-> Weather
"""

ERD = r"""
erDiagram
    USER {
        int id PK
        string username
        string email
        string first_name
        string last_name
        boolean is_staff
        boolean is_superuser
        boolean is_active
    }
    USERPROFILE {
        int id PK
        int user_id FK
        string role
        string phone_number
        string profile_picture
        string qualification_doc
        boolean is_verified
        text bio
    }
    REPORT {
        int id PK
        int user_id FK
        int assigned_to_id FK
        string incident_type
        string location
        datetime incident_date
        text description
        string priority
        string status
        boolean is_anonymous
        string evidence_file
        text admin_notes
        datetime created_at
        datetime updated_at
    }
    SUPPORTMESSAGE {
        int id PK
        int user_id FK
        string subject
        text message
        boolean is_read
        boolean is_read_by_user
        text admin_response
        datetime created_at
    }
    CHATMESSAGE {
        int id PK
        int support_thread_id FK
        int sender_id FK
        text message
        datetime created_at
    }
    SESSIONRECORDING {
        int id PK
        int student_id FK
        int counselor_id FK
        string title
        datetime date_recorded
        string video_file
        text notes
    }
    RESOURCE {
        int id PK
        string title
        text description
        string link
        string category
        string icon
        text content
        datetime created_at
    }
    ADMINLOG {
        int id PK
        int admin_id FK
        int report_id FK
        int user_affected_id FK
        string action
        text description
        datetime created_at
    }
    USER ||--|| USERPROFILE : has
    USER ||--o{ REPORT : submits
    USER o|--o{ REPORT : assigned_to
    USER ||--o{ SUPPORTMESSAGE : starts
    SUPPORTMESSAGE ||--o{ CHATMESSAGE : contains
    USER ||--o{ CHATMESSAGE : sends
    USER ||--o{ SESSIONRECORDING : student
    USER o|--o{ SESSIONRECORDING : counselor
    USER ||--o{ ADMINLOG : performs
    REPORT o|--o{ ADMINLOG : relates_to
    USER o|--o{ ADMINLOG : affected_user
"""

REPORT_ACTIVITY = r"""
flowchart TD
    A([Start: authenticated user]) --> B[Open report form]
    B --> C[Enter type, location, date/time, description]
    C --> D{Required fields present?}
    D -- No --> E[Show validation message; retain form]
    E --> C
    D -- Yes --> F{Evidence attached?}
    F -- No --> H[Create pending report]
    F -- Yes --> G{Size <= 10 MB and extension allowed?}
    G -- No --> I[Show warning; continue without evidence]
    I --> H
    G -- Yes --> J[Save evidence under local media]
    J --> H
    H --> K[Attempt email alert to verified security accounts]
    K --> L[Show success message and redirect to own reports]
    L --> M([End])
"""

REPORT_SEQUENCE = r"""
sequenceDiagram
    actor User
    participant Browser
    participant Django as Django View
    participant DB as MySQL
    participant Media as Local Media
    participant Email as Django Email
    User->>Browser: Complete report form
    Browser->>Django: POST form, CSRF token, optional file
    Django->>Django: Check required fields
    alt Required field missing
        Django-->>Browser: Validation message and form
    else Fields present
        opt Evidence attached
            Django->>Django: Check size and extension
            alt File acceptable
                Django->>DB: Save report
                Django->>Media: Save evidence file
            else File too large or unsupported
                Django-->>Browser: Warning; report continues without evidence
                Django->>DB: Save report without evidence
            end
        end
        Django->>DB: Find verified security profiles
        opt Verified officer has email
            Django->>Email: Attempt incident notification
        end
        Django-->>Browser: Success message and redirect to own reports
    end
"""

PANIC_ACTIVITY = r"""
flowchart TD
    A([Start: signed-in user]) --> B[Click Quick Exit]
    B --> C{Geolocation supported and permission granted?}
    C -- Yes --> D[Read latitude and longitude]
    C -- No --> E[Use null coordinates]
    D --> F[POST panic request in background]
    E --> F
    F --> G[Browser redirects to Google Weather Search]
    F --> H[Backend creates critical, pending report]
    H --> I[Query verified security profiles]
    I --> J{Officer has phone number?}
    J -- No --> K[Skip officer]
    J -- Yes --> L[POST SMS to BulkSMS]
    L --> M{HTTP 201?}
    M -- Yes --> N[Count as accepted]
    M -- No --> O[Log failure]
    K --> P([Return JSON to request if still connected])
    N --> P
    O --> P
"""

PANIC_SEQUENCE = r"""
sequenceDiagram
    actor User
    participant Browser
    participant Django as Django Backend
    participant DB as MySQL
    participant SMS as BulkSMS API
    participant Google as Google Weather Search
    User->>Browser: Click Quick Exit
    Browser->>Browser: Request GPS with 3-second timeout
    alt GPS acquired
        Browser->>Django: POST latitude and longitude (JSON, CSRF)
        Browser->>Google: Redirect immediately; does not await response
    else Denied, unavailable, or unsupported
        Browser->>Django: POST null coordinates
        Browser->>Google: Redirect immediately; does not await response
    end
    Django->>DB: Create critical, pending report
    Django->>DB: Query verified security officers
    DB-->>Django: Return officers
    loop Each officer with a phone number
        Django->>SMS: POST message and location
        alt HTTP 201
            SMS-->>Django: Accepted
        else Other response or connection error
            SMS-->>Django: Failure; backend logs and continues
        end
    end
    Django-->>Browser: JSON status, SMS count and location
"""

STATE = r"""
stateDiagram-v2
    [*] --> Pending: report created
    Pending --> Investigating: authorized handler changes status
    Pending --> Resolved: authorized handler changes status
    Pending --> Closed: authorized handler changes status
    Investigating --> Pending: authorized handler changes status
    Investigating --> Resolved: authorized handler changes status
    Investigating --> Closed: authorized handler changes status
    Resolved --> Pending: status can be changed in current UI
    Resolved --> Investigating: status can be changed in current UI
    Resolved --> Closed: authorized handler changes status
    Closed --> Pending: status can be changed in current UI
    Closed --> Investigating: status can be changed in current UI
    Closed --> Resolved: status can be changed in current UI
"""

CLASS_DIAGRAM = r"""
classDiagram
    class User {
        +id
        +username
        +email
        +is_staff
        +is_superuser
    }
    class UserProfile {
        +role
        +phone_number
        +is_verified
        +qualification_doc
        +profile_picture
        +bio
        +__str__()
    }
    class Report {
        +incident_type
        +location
        +incident_date
        +description
        +priority
        +status
        +is_anonymous
        +evidence_file
        +admin_notes
        +__str__()
    }
    class SupportMessage {
        +subject
        +message
        +is_read
        +is_read_by_user
        +admin_response
        +__str__()
    }
    class ChatMessage {
        +message
        +created_at
        +__str__()
    }
    class SessionRecording {
        +title
        +date_recorded
        +video_file
        +notes
        +__str__()
    }
    class Resource {
        +title
        +description
        +category
        +link
        +content
        +__str__()
    }
    class AdminLog {
        +action
        +description
        +created_at
        +__str__()
    }
    class ViewsModule {
        <<module>>
        +register_view()
        +new_report_view()
        +support_view()
        +admin_report_detail()
        +counselor_report_detail()
        +security_incident_detail()
        +trigger_panic()
    }
    class EmailUtilities {
        <<module>>
        +send_welcome_email()
        +send_report_assigned_notification()
        +send_status_update_notification()
        +send_counselor_response_notification()
    }
    User "1" --> "1" UserProfile
    User "1" --> "0..*" Report : submitted
    User "0..1" --> "0..*" Report : assigned
    User "1" --> "0..*" SupportMessage
    SupportMessage "1" *-- "0..*" ChatMessage
    User "1" --> "0..*" ChatMessage : sender
    User "1" --> "0..*" SessionRecording : student
    User "0..1" --> "0..*" SessionRecording : counselor
    User "1" --> "0..*" AdminLog : admin
    Report "0..1" --> "0..*" AdminLog
    ViewsModule ..> Report : ORM operations
    ViewsModule ..> EmailUtilities : notifications
"""


def build():
    doc = Document(TEMPLATE)
    reset_document(doc)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(36)
    r = p.add_run("SOFTWARE DEVELOPMENT PROJECT")
    r.bold = True
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor(23, 54, 93)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("FINAL PROJECT REPORT")
    r.bold = True
    r.font.size = Pt(24)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("SafeCampus GBV System")
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor(31, 78, 121)
    add_para(doc, "")
    for line in [
        "Prepared by: Student Name (replace before submission)",
        "Student number: Student Number (replace before submission)",
        "Department of Computer Science & Information Technology",
        "Sol Plaatje University",
        "",
        "Submitted to: Dr Silas Verkijika",
        "Lecturer: Project (NPRJ740)",
        "Department of Computer Science & Information Technology",
        "Sol Plaatje University",
        "24-26 Scanlan St, New Park, Kimberley, 8301",
        "",
        f"Submission date: {DATE}",
    ]:
        p = add_para(doc, line)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    heading(doc, "EXECUTIVE SUMMARY")
    add_para(doc, "SafeCampus is a web-based gender-based violence (GBV) reporting and support application developed for a university community. It addresses the difficulty of providing a structured channel for incident reports, case follow-up, support conversations, and urgent notifications. The intended users are students, staff, counselors, security officers, administrators, and public visitors using account and contact pages.")
    add_para(doc, "The reviewed codebase implements account registration and authentication, user profiles and verification, report submission and tracking, evidence uploads, support conversations, role-oriented dashboards, report assignment and status updates, resources, session recording uploads, email notifications, and a Quick Exit panic workflow. The application is a Django monolith using server-rendered templates, Django ORM models, a MySQL database configuration, local media storage, EmailJS in the registration page, Django email utilities, and a BulkSMS HTTP integration.")
    add_para(doc, "This report documents the implementation as inspected on 6 November 2026. It is not a claim that the system is production-ready: the test module is only a placeholder, the Django system check could not start because PyMySQL is missing in the configured environment, and production security settings and credentials require remediation. Student name and number, real project evidence, screenshots, and executed test results must be added by the author before submission.")

    heading(doc, "PROJECT CONTEXT")
    add_para(doc, "The project is in the campus safety, GBV reporting, and student-support domain. The application is intended to give a university community an online pathway to report incidents, communicate with support personnel, and receive case follow-up. It provides a Rapid Quick Exit action for authenticated users, which attempts to capture browser geolocation, creates a critical report, and sends SMS messages to verified security accounts that have phone numbers.")
    add_para(doc, "The implementation references Sol Plaatje University in its interface and email content. This report treats SafeCampus as an academic project/application associated with that context; it does not assert that the university has formally adopted or operationally approved the system. No interview transcripts, survey findings, stakeholder sign-off, or institutional policy documents were present in the materials inspected. The problem rationale is therefore based on the stated project purpose and implemented workflows, and should be strengthened with approved stakeholder evidence.")

    heading(doc, "PROBLEM, PURPOSE AND SUCCESS CRITERIA")
    heading(doc, "Problem Statement", 2)
    add_para(doc, "People affected by GBV or related safety incidents may need a discreet, accessible way to report an incident, attach relevant evidence, contact support, and follow up. A process that relies only on in-person reporting or disconnected communication channels can make it harder to submit information and coordinate a response. Students and staff are the primary reporters; counselors, security officers, and administrators need a controlled workflow to review, assign, and manage cases.")
    add_para(doc, "The software problem is to provide one web application for these workflows while protecting personal and incident information. The codebase demonstrates reporting, support messaging, assignment, role-specific screens, and an emergency alert workflow. The project materials supplied do not contain empirical needs-assessment data, so no prevalence claims or measured user pain points are asserted.")
    heading(doc, "Project Purpose", 2)
    add_para(doc, "The purpose is to implement and evaluate a web application that supports incident reporting, case administration, counselor/security response, user support conversations, safety resources, and emergency notification for a university community.")
    heading(doc, "Success Criteria", 2)
    add_table(doc, ["ID", "Success criterion", "Evidence required"], [
        ("SC-01", "An authenticated user can submit a valid report and retrieve their own report and status.", "Demonstration and automated tests for required fields, persistence, and ownership."),
        ("SC-02", "Authorized staff can review, assign, and update reports, while role restrictions are verified.", "Role-based access tests for administrator, counselor, security, and ordinary user."),
        ("SC-03", "Support messages can be sent and replies can be associated with the correct thread.", "Create/reply/read test with database assertions."),
        ("SC-04", "Quick Exit creates a critical report and handles location/SMS success and failure cases safely.", "Mocked geolocation and BulkSMS tests; live SMS only with consent and test recipients."),
        ("SC-05", "The release passes project checks and documented functional/security test cases.", "Successful environment check, test run, and completed evidence table.")
    ])
    add_para(doc, "These criteria are proposed verification targets. The current repository does not include evidence that they have all been met.")

    heading(doc, "SOLUTION OVERVIEW AND SCOPE")
    heading(doc, "Solution Overview", 2)
    add_para(doc, "SafeCampus is a browser-based, server-rendered Django application. A visitor can access account registration, login, password reset, and contact support. Authenticated users are routed according to profile role or Django staff/superuser flags. Django view functions process forms and JSON requests, use ORM models to persist records, save uploaded media beneath the configured local media root, and invoke configured email or SMS integrations.")
    add_para(doc, "The system boundary includes the browser interface, Django application, authentication/session middleware, dashboard application models and views, relational database, and configured local file storage. External interactions include the browser Geolocation API, EmailJS from the registration page, Django email backend, BulkSMS REST API, and a Google weather search redirect after Quick Exit. Google Weather is a browser redirect target, not a backend data service.")
    add_mermaid(doc, "System context diagram (Mermaid source)", CONTEXT, "Paste the source into a Mermaid editor to render the diagram.")
    heading(doc, "3.2 Final Release Scope", 2)
    add_table(doc, ["Capability", "Release status", "Implementation summary"], [
        ("Registration, login, logout, password reset", "Included, with limitations", "Django authentication; selected staff roles require verification; registration template also invokes EmailJS."),
        ("Profile maintenance and staff qualification upload", "Included", "Profile fields and local qualification document storage; admin verification endpoint."),
        ("Incident reporting and report tracking", "Included", "Authenticated form, report list/detail, category, location, date, description, anonymous flag, priority/status."),
        ("Evidence upload", "Included, limited", "Extension and 10 MB checks in report view; local media storage."),
        ("Support conversations", "Included", "Support thread and chat-message records; user and counselor/admin interfaces."),
        ("Admin report/user/resource management", "Included", "Report filtering, assignment, priority/status changes, user controls, resources and activity-log views."),
        ("Counselor/security response", "Included, limited", "Role dashboards, report status/notes, counselor messaging and security incident view."),
        ("Session recordings", "Included, limited", "Counselor upload and student listing; file constraints and access controls need further verification."),
        ("Quick Exit / Panic Button", "Included, external delivery unverified", "Creates critical report, queries verified officers, attempts BulkSMS, redirects browser."),
        ("Email and SMS notifications", "Included, configuration dependent", "EmailJS client-side registration template, Django email functions and BulkSMS call; actual delivery depends on setup.")
    ])
    heading(doc, "3.3 Excluded and Deferred Capabilities", 2)
    add_table(doc, ["Capability", "Disposition", "Reason / boundary"], [
        ("Production deployment and institutional adoption", "Deferred", "No deployment target, approval, operational owner, or production runbook was supplied."),
        ("Native mobile application", "Excluded from current release", "The reviewed system is a web application."),
        ("Automated GPS tracking beyond Quick Exit", "Excluded", "Location is collected only through the browser panic workflow; no continuous tracking is implemented."),
        ("Real-time chat/WebSocket delivery", "Deferred", "Chat is implemented with normal web requests and persisted messages, not a real-time socket service."),
        ("Analytics, export, and formal outcome reporting", "Deferred", "No dedicated reporting/export module was identified."),
        ("External identity provider / MFA", "Deferred", "No SSO, multi-factor, or university directory integration was identified."),
        ("Cloud object storage and backup automation", "Deferred", "Files use local media storage; no cloud object store or backup job was identified."),
        ("Automated matching of cases to specialist responders", "Excluded", "Assignments are made through administrator UI; no matching engine exists.")
    ])
    heading(doc, "3.4 Known Limitations and Open Issues", 2)
    add_table(doc, ["Issue", "Impact", "Status / action"], [
        ("Configured development environment lacks PyMySQL.", "manage.py check fails during Django initialization before application checks run.", "Install declared DB driver, add dependency manifest, configure database, rerun checks."),
        ("Test module contains only the default empty TestCase.", "No automated evidence validates main workflows.", "Add unit, integration, permissions, upload, and panic tests before claiming completion."),
        ("Production settings are unsafe or incomplete: DEBUG is enabled, ALLOWED_HOSTS is empty, and a placeholder secret is configured.", "Not suitable for public deployment.", "Use environment-specific secure settings and Django deployment checklist."),
        ("BulkSMS credentials are hardcoded in source.", "Exposes a live-service credential if the source is shared.", "Rotate credentials; use environment variables/secret storage; never put values in this report."),
        ("Quick Exit browser fetch is not awaited before navigation.", "Navigation can interrupt the request; successful alert creation/delivery is not guaranteed.", "Use a reliable acknowledged workflow (e.g. beacon/keepalive plus server confirmation) and test in browsers."),
        ("Report anonymous flag does not remove report.user association.", "Authorized application users may still see the reporter; this is not fully anonymous reporting.", "Describe accurately, restrict access, and redesign privacy rules if true anonymity is required."),
        ("Counselor, security, or admin detail views do not consistently constrain records to assigned cases.", "Role access may be broader than least privilege.", "Enforce object-level authorization for every detail/action endpoint."),
        ("Report form checks file extension/size but not content signature; session video has no explicit per-file policy in the view.", "Malicious or oversized content may be stored; uploaded media can expose sensitive data.", "Enforce content/type/size policy, private storage, and safe download authorization."),
        ("Several notification calls suppress mail errors or only log exceptions.", "UI success may not mean notifications were delivered.", "Add durable delivery status/retry/monitoring and truthful delivery feedback."),
        ("The report view attempts security email alerts, while panic uses BulkSMS; EmailJS and Django email are both present.", "Multiple email pathways can cause inconsistent behavior/configuration.", "Document and consolidate provider responsibilities.")
    ])

    heading(doc, "SYSTEM REQUIREMENTS SPECIFICATION")
    heading(doc, "Functional Requirements", 2)
    fr = [
        ("FR-01", "The system shall allow a visitor to register with a username, email, role, and password and require terms acceptance.", "Must-Have", "Included"),
        ("FR-02", "The system shall authenticate users, create authenticated sessions, and allow logout.", "Must-Have", "Included"),
        ("FR-03", "The system shall prevent unverified counselor, security, and staff profiles from logging in, subject to the configured superuser exception.", "Must-Have", "Included"),
        ("FR-04", "The system shall allow password-reset requests and token-based password changes.", "Should-Have", "Included; delivery not verified"),
        ("FR-05", "The system shall allow authenticated users to update profile details and upload permitted profile/qualification files.", "Should-Have", "Included; validation limited"),
        ("FR-06", "The system shall accept incident type, location, incident date/time, description, and anonymous preference for a report.", "Must-Have", "Included"),
        ("FR-07", "The system shall validate report required fields and store accepted reports with an initial pending status.", "Must-Have", "Included"),
        ("FR-08", "The system shall accept optional evidence only when its configured size and extension checks pass.", "Should-Have", "Included; security validation incomplete"),
        ("FR-09", "The system shall allow a reporting user to list and view their own reports.", "Must-Have", "Included"),
        ("FR-10", "The system shall allow administrators to filter reports and update assignment, priority, status, and notes.", "Must-Have", "Included; object-level rules need review"),
        ("FR-11", "The system shall allow counselors to review cases, update status, add notes, and respond to support threads.", "Must-Have", "Included; object-level rules need review"),
        ("FR-12", "The system shall allow security users to view incidents, update status, and add notes.", "Must-Have", "Included; object-level rules need review"),
        ("FR-13", "The system shall allow users to create support threads and persist messages from identified senders.", "Must-Have", "Included"),
        ("FR-14", "The system shall allow counselors to upload a session recording associated with a student and allow students to view their recordings.", "Should-Have", "Included; access/file policy needs verification"),
        ("FR-15", "The system shall allow users to browse resource entries and administrators to add or delete them.", "Should-Have", "Included"),
        ("FR-16", "The Quick Exit endpoint shall create a critical pending report and attempt SMS delivery to verified security profiles with phone numbers.", "Must-Have", "Included; end-to-end reliability unverified"),
        ("FR-17", "The system shall send configured welcome, support, assignment, and status email notifications.", "Should-Have", "Partial; provider configuration and delivery unverified"),
        ("FR-18", "The system shall allow administrators to verify selected profiles, manage users, and review activity records.", "Should-Have", "Included; activity logging coverage is incomplete")
    ]
    add_table(doc, ["ID", "Functional requirement", "Priority", "Release status"], fr)
    heading(doc, "Non-Functional Requirements", 2)
    nfr = [
        ("NFR-01", "Security", "Only authenticated users shall access protected application pages; admin actions shall require staff/superuser authorization.", "Automated role and anonymous-access tests", "Implemented in part; endpoint coverage needs tests"),
        ("NFR-02", "Privacy", "Reports and support content shall be visible only to authorized participants and handlers.", "Object-level access tests across roles", "Not demonstrated; restrictions need review"),
        ("NFR-03", "Password handling", "Passwords shall be stored using Django's password-hashing mechanisms, never as plaintext.", "Inspect user creation/authentication and database values", "Django auth used; confirm stored values"),
        ("NFR-04", "File handling", "Uploads shall enforce allowed type and size and shall not be publicly accessible without authorization.", "Boundary, MIME/signature, and access tests", "Partial; local media and incomplete checks"),
        ("NFR-05", "Reliability", "Critical panic reports shall be persisted and alert attempts observable even if SMS delivery fails.", "Mock provider failures and verify report persistence/logging", "Partial; fetch navigation race and logging-only failures"),
        ("NFR-06", "Compatibility", "Core workflows shall operate on supported current Chrome and Edge versions.", "Manual browser test matrix", "Not tested in supplied repository"),
        ("NFR-07", "Usability", "Core forms shall identify required fields and present understandable validation feedback.", "Task-based review and validation tests", "Partially implemented in forms"),
        ("NFR-08", "Maintainability", "Runtime dependencies and setup steps shall be reproducible from a dependency manifest.", "Fresh-environment setup test", "Not met; no dependency manifest identified"),
        ("NFR-09", "Availability", "Production deployment shall use a supported host, database backup, monitoring, and secure configuration.", "Deployment review and recovery test", "Not in current release"),
        ("NFR-10", "Performance", "Normal page actions should complete within an agreed response-time target under expected load.", "Define workload and run a repeatable load test", "Target and performance evidence not yet established")
    ]
    add_table(doc, ["ID", "Attribute", "Requirement", "Verification", "Current evidence"], nfr, font_size=7.6)
    heading(doc, "Business Rules", 2)
    rules = [
        ("BR-01", "A report is linked to its submitting Django User, including when is_anonymous is selected."),
        ("BR-02", "New ordinary reports default to pending status and medium priority unless explicitly assigned otherwise."),
        ("BR-03", "A panic-button report is created as incident_type other, priority critical, and status pending."),
        ("BR-04", "Counselor, security, and staff registrations require administrator verification before login; superuser has an exception."),
        ("BR-05", "A report may have at most one assigned_to user; the assignee may be null."),
        ("BR-06", "Report status values are pending, investigating, resolved, and closed; current UI allows selection without an enforced transition graph."),
        ("BR-07", "Report evidence is optional; current view checks a 10 MB maximum and filename extensions."),
        ("BR-08", "Panic SMS recipients are profiles with security role and is_verified=true, and a non-empty phone number."),
        ("BR-09", "Support chat messages belong to one support thread and reference the sender."),
        ("BR-10", "Session recordings reference a student and may reference a counselor; counselor is nullable."),
        ("BR-11", "The UI's anonymous-report wording must not be interpreted as database anonymity without a redesigned identity model/access policy."),
    ]
    add_table(doc, ["ID", "Business rule"], rules)
    heading(doc, "Acceptance Criteria for Included Requirements", 2)
    acceptance = [
        ("FR-01/03 Registration and verification", ["Valid registration stores a user/profile; missing terms, mismatched passwords, short passwords, duplicate username/email are rejected with feedback.", "Student can sign in after registration.", "Unverified staff/counselor/security cannot sign in; administrator verification permits the intended access."]),
        ("FR-06/08 Submit report", ["A valid authenticated submission persists its required details and pending status.", "Missing required data is rejected.", "Allowed evidence within 10 MB is associated with report; oversized or disallowed extension is not saved and produces a warning.", "Reporter can find the report in their own list."]),
        ("FR-09 Report privacy", ["User A can access their own report.", "User B cannot retrieve User A's report detail.", "Test as staff, counselor, security, and administrator and document each allowed access path."]),
        ("FR-10/11/12 Case management", ["Authorized handler can set a valid status, assignment where applicable, priority, and notes.", "Unauthorized role is denied.", "Status update notification is attempted only when configured and its delivery result is observable."]),
        ("FR-13 Support chat", ["User can open a thread and its first message is recorded.", "Reply is stored under the selected thread with the correct sender.", "Unrelated user cannot read or reply to the thread."]),
        ("FR-14 Session recordings", ["Authorized counselor can upload a recording for a selected student.", "Metadata and file are stored together.", "Only the associated student and authorized counselor can access the recording."]),
        ("FR-16 Panic alert", ["With coordinates, endpoint stores map link and critical priority.", "Without coordinates, report is still created with unavailable-location text.", "Verified officers with phones are attempted; missing phone and provider failure do not erase the incident.", "Browser redirect and request delivery behavior are verified on target browsers."]),
    ]
    for title, criteria in acceptance:
        heading(doc, title, 3)
        add_bullets(doc, criteria)

    heading(doc, "SYSTEM DESIGN SPECIFICATION")
    heading(doc, "Use Cases and Workflows", 2)
    add_para(doc, "Principal actors are Visitor, Student, Staff, Counselor, Security Officer, and Administrator. Administrator is determined by Django staff/superuser flags and is not one of the UserProfile role choices. The use-case representation below focuses on the capabilities found in the repository.")
    add_mermaid(doc, "Use-case diagram (flowchart representation)", USE_CASE, "Mermaid does not define a standard usecaseDiagram grammar; this flowchart is the equivalent actor-to-capability view.")
    add_para(doc, "Workflow 1: a signed-in user submits an incident report. The backend checks required fields, optionally validates and stores evidence, persists a pending report, attempts security email notification, and returns the user to their report list. Invalid/oversized evidence has an alternate path.")
    add_mermaid(doc, "Activity diagram: submit incident report", REPORT_ACTIVITY)
    add_mermaid(doc, "Sequence diagram: submit incident report", REPORT_SEQUENCE)
    add_para(doc, "Workflow 2: an authenticated user triggers Quick Exit. Browser geolocation may succeed or fail. The browser sends the JSON request and immediately navigates to Google Weather Search; the Django endpoint persists a critical report, queries verified security profiles, and attempts BulkSMS calls.")
    add_mermaid(doc, "Activity diagram: Quick Exit", PANIC_ACTIVITY)
    add_mermaid(doc, "Sequence diagram: Quick Exit", PANIC_SEQUENCE, "The frontend does not wait for the POST response before changing location; therefore the diagram does not imply guaranteed delivery.")
    add_mermaid(doc, "Report lifecycle state diagram", STATE, "This diagram reflects the status options in the current UI. The application does not enforce a restricted transition policy; authorized handlers can select statuses from the available choices.")

    heading(doc, "System Architecture and Technology Stack", 2)
    add_para(doc, "The codebase follows a monolithic Django pattern. Django views handle request/response orchestration, Django ORM models represent persistent data, templates render HTML, and JavaScript performs browser geolocation, EmailJS registration notification, and the asynchronous panic POST. The database is configured as MySQL. The repository also contains a SQLite database file, but the inspected Django settings point to MySQL; do not assume the SQLite file is the active runtime database.")
    add_mermaid(doc, "Logical architecture diagram", ARCHITECTURE)
    add_table(doc, ["Component", "Technology / configuration", "Responsibility"], [
        ("Browser UI", "Django templates, HTML, CSS, Bootstrap-related classes, JavaScript", "Forms, dashboards, geolocation prompt, frontend EmailJS welcome message, Quick Exit redirect."),
        ("Web application", "Python 3.13 environment; Django 6.0.6 project", "Routing, authentication, request validation, business workflows, rendered responses."),
        ("Dashboard app", "Django app `dashboard`", "Models, role views, notification helpers, report/support/admin workflows."),
        ("Authentication", "Django auth User, sessions, middleware", "Login/logout, password validation, authorization decorators and role checks."),
        ("Persistence", "MySQL backend configured in settings", "Relational data through Django ORM."),
        ("File storage", "Local `MEDIA_ROOT`", "Evidence, qualification docs, profile images, session videos."),
        ("SMS", "BulkSMS HTTP JSON API", "Attempts panic alerts to verified security users with phone numbers."),
        ("Email", "EmailJS browser SDK plus Django email utilities; console backend in dev", "Registration welcome mail and configured workflow notifications."),
        ("External navigation", "Browser geolocation and Google Weather Search URL", "Panic location acquisition and stealth-style browser navigation.")
    ])
    heading(doc, "Key Architecture and Design Decisions", 2)
    decisions = [
        ("ADR-01 Relational persistence", "Context: reports, users, messages, and assignments have structured relationships. Options: relational SQL or document storage. Decision: Django ORM with configured MySQL. Rationale: foreign keys and relational queries suit the modeled relationships. Consequence: requires a running MySQL server and compatible driver; current configured Python environment lacks PyMySQL."),
        ("ADR-02 Monolithic web application", "Context: one academic web application has several role workflows. Options: monolith or independent services. Decision: a single Django project/app. Rationale: simpler deployment and shared authentication/data model. Consequence: views have multiple responsibilities and the project needs modularization as it grows."),
        ("ADR-03 Local file storage", "Context: evidence and session videos are uploaded. Decision: Django local media storage. Rationale: straightforward development setup. Consequence: deployment needs access control, backups, storage limits, and a non-public serving strategy."),
        ("ADR-04 Hybrid notification integrations", "Context: email and panic alerts need external delivery. Decision: EmailJS in registration template, Django email helpers, and BulkSMS REST call. Consequence: configuration is split; email behavior may be duplicated and delivery is not verified end-to-end."),
        ("ADR-05 Django session authentication", "Context: web UI is server-rendered. Decision: use Django authentication and sessions. Consequence: CSRF protections and secure cookie/deployment settings must remain correctly configured.")
    ]
    for title, description in decisions:
        add_para(doc, f"{title}: {description}", bold_prefix=title)

    heading(doc, "Application Class Design", 2)
    add_para(doc, "The application is primarily function-based: views are module-level functions, not service classes. The class diagram therefore shows Django model classes and key view/email modules as modules rather than inventing classes that are not in the source.")
    add_mermaid(doc, "Class diagram", CLASS_DIAGRAM)
    add_table(doc, ["Class / module", "Responsibilities"], [
        ("User (Django)", "Authentication identity, username/email, staff/superuser flags."),
        ("UserProfile", "One-to-one role, verification state, contact details, qualification and profile files."),
        ("Report", "Incident details, reporter, assignee, status, priority, evidence and notes."),
        ("SupportMessage / ChatMessage", "Support thread data, read markers, initial message and sender-attributed conversation messages."),
        ("SessionRecording", "Student/counselor association, recording file, title, date and notes."),
        ("Resource", "Support/education resource metadata and content."),
        ("AdminLog", "Audit-style action record and optional report/affected-user links; coverage is not comprehensive."),
        ("views module", "Function-based HTTP handlers for registration, reports, dashboards, support, panic, etc."),
        ("emails module", "Email helper functions for welcome, support, assignment, and status notifications.")
    ])
    heading(doc, "User Interface and Interaction Design", 2)
    add_para(doc, "The interface uses role-oriented dashboard templates and shared navigation. The shared authenticated navigation includes a Quick Exit action. The report form collects incident type, location, date/time, description, optional evidence, and anonymous preference. Admin/counselor/security pages expose case actions, while support pages present thread lists and conversations.")
    add_para(doc, "Screenshots are not included because no running browser session or approved sample account was supplied. Capture actual application screenshots with synthetic/demo data, remove personal identifiers, and insert them below before submission. Do not use real survivor cases or credentials.")
    add_table(doc, ["Screenshot to insert", "User / purpose", "Requirement or state"], [
        ("[Insert screenshot: login and registration]", "Visitor; show entry point and role selection.", "FR-01 to FR-03; include validation error if available."),
        ("[Insert screenshot: report form]", "Student; show incident details and evidence control.", "FR-06 to FR-08."),
        ("[Insert screenshot: report submission result/list]", "Student; show successful persisted report and status.", "FR-07, FR-09."),
        ("[Insert screenshot: case assignment]", "Administrator; show report assignment/status controls.", "FR-10, FR-18."),
        ("[Insert screenshot: counselor or security case page]", "Secondary responder; show case review and notes/status action.", "FR-11 or FR-12."),
        ("[Insert screenshot: support conversation]", "User and responder; show messages in one thread.", "FR-13."),
        ("[Insert screenshot: validation/error]", "Any user; show actual required-field, duplicate, or upload error.", "Relevant validation requirement."),
        ("[Insert screenshot: Quick Exit response]", "Synthetic test account; show UI behavior without live alert credentials.", "FR-16; never trigger a real emergency alert during capture.")
    ])
    heading(doc, "Data Design", 2)
    add_para(doc, "Django ORM models in `dashboard/models.py` define the application data. Settings configure MySQL with UTF-8 support. A local `db.sqlite3` file is present in the project directory, but the configured database engine is MySQL; runtime connectivity has not been validated. Files use Django FileField/ImageField paths beneath `MEDIA_ROOT` and are stored separately from relational metadata.")
    add_mermaid(doc, "Entity-relationship diagram", ERD)
    add_table(doc, ["Entity", "Important attributes and constraints", "Purpose"], [
        ("User", "Django auth identity; unique username; email/name and staff/superuser/active flags.", "Login and ownership/actor identity."),
        ("UserProfile", "OneToOne to User; role; nullable/blank phone, bio, picture and qualification file; is_verified.", "Role and supplementary account data."),
        ("Report", "FK reporter; optional FK assignee (SET_NULL); incident type, location, date/time, description, priority, status, anonymity flag, optional file and notes.", "Incident case and lifecycle."),
        ("SupportMessage", "FK user; subject/message; read flags; optional admin_response; creation time.", "Support thread summary and response tracking."),
        ("ChatMessage", "FK support thread; FK sender; message and creation time.", "Individual conversation entries."),
        ("SessionRecording", "FK student; nullable FK counselor; title, date, optional video file and notes.", "Session recording metadata."),
        ("Resource", "Title, description, optional URL/content, category, icon and created time.", "Support/education materials."),
        ("AdminLog", "FK admin; optional report and affected user; action, description and creation time.", "Selected administrative activity.")
    ])
    add_para(doc, "Data integrity is primarily provided by Django model relations and the database foreign keys, including one-to-one profile association, report assignment set-null behavior, and cascade behavior on several related records. Business validation is also performed in views. No explicit indexes beyond Django's primary/foreign-key conventions, retention schedule, backup process, encrypted file storage, or database transaction strategy was identified. These are operational requirements for a production deployment.")
    heading(doc, "Data Dictionary (selected fields)", 3)
    add_table(doc, ["Field", "Type / nullability", "Key / purpose"], [
        ("User.id", "Auto integer; required", "Primary key."),
        ("User.username", "String; required", "Unique login name."),
        ("User.email", "Email/string; generally optional in Django model", "Contact/notification address."),
        ("UserProfile.user_id", "One-to-one FK; required", "Links profile to Django User."),
        ("UserProfile.role", "String choice; required; defaults student", "student, staff, counselor, security."),
        ("UserProfile.is_verified", "Boolean; required; defaults false", "Staff-role verification gate."),
        ("Report.user_id", "FK; required", "Submitting user; still populated for anonymous-flag reports."),
        ("Report.assigned_to_id", "Nullable FK", "Current report assignee."),
        ("Report.incident_type", "String choice; required", "Harassment, assault, bullying, discrimination, sexual harassment, physical/verbal abuse, stalking, other."),
        ("Report.location / incident_date / description", "String / datetime / text; required", "Incident information."),
        ("Report.priority / status", "String choices; required; medium/pending defaults", "Severity and workflow state."),
        ("Report.evidence_file", "Optional FileField path", "Evidence stored in media/evidence/."),
        ("SupportMessage.user_id", "FK; required", "Thread owner."),
        ("ChatMessage.support_thread_id / sender_id", "FKs; required", "Thread and message author."),
        ("SessionRecording.student_id / counselor_id", "FK / nullable FK", "Participants; video file is optional in model."),
        ("Resource.link / content", "Optional URL/text", "External destination and resource body.")
    ], font_size=7.8)
    heading(doc, "Security, Privacy and Access Control", 2)
    add_para(doc, "Authentication uses Django's built-in user model and session authentication. Login applies a verification check for counselor, security, and staff profiles, except superusers. Admin views use `login_required` plus `user_passes_test(is_admin)`. Role-specific pages have explicit role checks in view code, but several object detail handlers do not consistently confirm that the selected report or message is assigned to, owned by, or otherwise authorized for that user.")
    add_table(doc, ["Function", "Student", "Staff", "Counselor", "Security", "Administrator"], [
        ("Register / sign in", "Yes", "Yes; verify", "Yes; verify", "Yes; verify", "Yes"),
        ("Submit report / evidence", "Yes", "Yes", "Authenticated route", "Authenticated route", "Authenticated route"),
        ("View own reports", "Yes", "Yes where routed", "No general own-report screen", "No general own-report screen", "All reports"),
        ("Support chat", "Create/reply own threads", "Create/reply own threads", "View/reply (current view broad)", "Not clearly provided", "Manage/respond"),
        ("Handle report / add notes", "No", "Some security detail access", "Yes (role check)", "Yes (role check)", "Yes"),
        ("Assign / change priority", "No", "No", "No", "No", "Yes"),
        ("Verify profiles / manage users", "No", "No", "No", "No", "Yes"),
        ("Upload session recording", "No", "No", "Yes", "No", "No specific workflow"),
        ("View student recordings", "Own listed recordings", "No", "Counselor listing page", "No", "No specific workflow"),
        ("Trigger Quick Exit", "Yes when authenticated", "Yes when authenticated", "Yes when authenticated", "Yes when authenticated", "Yes when authenticated")
    ], font_size=7.3)
    add_para(doc, "Matrix note: a cell marked 'authenticated route' means the URL is protected by login but may not have a dedicated role restriction. The current code should be hardened to an explicit least-privilege policy before deployment.")
    add_table(doc, ["Area", "Risk", "Observed control / required action"], [
        ("Authentication", "Account takeover or unauthorized use.", "Django auth and sessions are used. Add MFA/SSO only if required; configure secure cookies, HTTPS, session expiry."),
        ("Authorization", "Cross-user report/message access.", "Decorator and role checks exist; add object-level authorization to every detail/read/write endpoint and test each role."),
        ("Password storage", "Plaintext credential exposure.", "Django auth user creation is used; confirm password hashing path and never store/log plaintext."),
        ("CSRF", "Cross-site form/API actions.", "Django CSRF middleware and template tokens are present; confirm all browser POSTs include valid tokens."),
        ("Uploads", "Malicious content or sensitive file disclosure.", "Some size/extension checks exist; add content validation, private storage, randomized names, quotas, authorization on download."),
        ("Secrets", "SMS/API credential compromise.", "Credential is present in code; rotate it and move secrets to protected environment/secret store."),
        ("Production configuration", "Debug leakage and insecure host/cookie configuration.", "DEBUG is enabled and SECRET_KEY is placeholder; use production settings and run deployment checks."),
        ("Privacy", "Misleading anonymity and overexposure of GBV data.", "Anonymous flag does not detach identity. Restrict access, explain privacy accurately, and define retention/deletion policy."),
        ("Logging/audit", "Sensitive incident data or secrets in logs.", "Some print-based logs include user/phone details and failures. Replace with structured, redacted logs and comprehensive audit trail."),
        ("Notifications", "False delivery confidence or disclosure via email/SMS.", "Some mail errors are suppressed; avoid sensitive narrative in notifications and store delivery results.")
    ], font_size=7.5)
    heading(doc, "Deployment and Runtime Design", 2)
    add_para(doc, "The project is configured for a local development run with Django and a MySQL server. The deployed architecture, domain, TLS termination, process manager, static asset server, backup schedule, and monitoring are not specified. A populated environment file and production configuration are required; do not commit database/SMS credentials.")
    add_numbered(doc, [
        "Install the supported Python runtime and create/activate a virtual environment.",
        "Install dependencies from a maintained requirements file. No such dependency manifest was identified; currently the configured environment is missing PyMySQL, so Django initialization fails.",
        "Install and start MySQL, create the application database, and configure database credentials through environment variables.",
        "Set a unique secret key, DEBUG=False, ALLOWED_HOSTS, secure CSRF/session cookie options, and HTTPS settings for deployment.",
        "Apply Django migrations, create an administrator account, and configure private media storage and backups.",
        "Configure EmailJS and Django email intentionally, and configure BulkSMS credentials in a secret store. Use test recipients and provider mocks during testing.",
        "Run `python manage.py check`, `python manage.py test`, then a deployment checklist and browser acceptance tests."
    ])

    heading(doc, "SYSTEM IMPLEMENTATION")
    heading(doc, "Codebase and Repository Structure", 2)
    add_table(doc, ["Path", "Responsibility"], [
        ("gbv_system/settings.py", "Django settings, middleware, database, email, static/media configuration."),
        ("gbv_system/urls.py", "Project-level admin and dashboard URL inclusion."),
        ("dashboard/models.py", "Report, profile, support, chat, resource, activity and recording models."),
        ("dashboard/views.py", "Request handlers for account, dashboards, reports, support, administration, sessions and panic."),
        ("dashboard/urls.py", "Named application routes."),
        ("dashboard/emails.py", "Django email notification helpers."),
        ("dashboard/context_processors.py", "Role-specific navigation notification data."),
        ("dashboard/migrations/", "Schema migration history."),
        ("templates/", "Server-rendered HTML screens and browser scripts."),
        ("media/", "Local user-uploaded media directory."),
        ("static/", "Static frontend assets.")
    ])
    heading(doc, "Implementation of Core Capabilities", 2)
    add_table(doc, ["Capability", "Requirements", "Main implementation components"], [
        ("Account and profile", "FR-01 to FR-05", "dashboard.views register/login/logout/profile/password reset; UserProfile; registration/profile templates."),
        ("Incident submission", "FR-06 to FR-09", "new_report_view, reports_view, report_detail_view; Report model; new_report/reports templates."),
        ("Administration", "FR-10, FR-18", "admin_dashboard, admin_reports, admin_report_detail, admin users/resources/activity views; AdminLog."),
        ("Counseling/security", "FR-11 to FR-13", "counselor and security views; SupportMessage and ChatMessage models."),
        ("Recordings/resources", "FR-14 to FR-15", "counselor_upload_recording, my_sessions, resources views; SessionRecording and Resource."),
        ("Panic alerts", "FR-16", "base.html Quick Exit JavaScript; trigger_panic JSON view; BulkSMS HTTP POST; Report model."),
        ("Notifications", "FR-17", "EmailJS registration template; dashboard.emails Django helpers; BulkSMS integration.")
    ])
    heading(doc, "APIs, Integrations and External Dependencies", 2)
    add_table(doc, ["Integration", "Direction and use", "Constraints / status"], [
        ("BulkSMS API", "Backend POST to `/v1/messages` for panic notifications.", "Requires working credentials, network and verified recipient phone numbers; no live end-to-end test evidence."),
        ("EmailJS Browser SDK", "Registration template submits a welcome-email template using client-side service/template/public identifiers.", "Client-side provider configuration; do not treat as secure secret storage; success/failure only logged in browser."),
        ("Django email backend", "Welcome, assignment, support, report status and contact-support mail.", "Development backend is console; SMTP settings are placeholders/commented. Some sends use fail_silently."),
        ("MySQL", "Django ORM persistence.", "Configured in settings; environment check is blocked by missing PyMySQL."),
        ("Browser Geolocation", "Quick Exit requests latitude/longitude after user clicks and grants permission.", "Browser permission and supported secure context required; fallback omits coordinates."),
        ("Google Weather Search", "Browser redirect after Quick Exit.", "External navigation only; no weather data integration."),
        ("Microsoft Teams / mailto", "Template links for contacting a reporter/counselor.", "External link handoff; requires user account/app.")
    ])
    heading(doc, "AI / Machine-Learning Component (where applicable)", 2)
    add_para(doc, "No AI or machine-learning component was identified in the inspected source code. Case assignment and report handling are manual; the system does not make automated risk decisions.")

    heading(doc, "VERIFICATION AND TESTING")
    heading(doc, "Test Approach", 2)
    add_para(doc, "Verification should combine Django unit tests for models and validation, request-level tests for access control and workflows, mocked integration tests for EmailJS/BulkSMS boundaries, file-upload tests, and manual browser tests for geolocation/navigation. Live SMS or email must not be sent to real users during testing. The repository's `dashboard/tests.py` contains only the default placeholder test case.")
    add_para(doc, "Execution status: `python manage.py check` was attempted using the project's configured virtual environment. It failed before application checks because `gbv_system/__init__.py` imports `pymysql`, which is not installed. No claim is made that unit tests or real integrations passed.")
    heading(doc, "Functional and Business-Rule Verification", 2)
    test_rows = [
        ("T-01", "FR-01 / BR-04", "Register student with valid data; then try missing terms, mismatch, short password, duplicates.", "Django client / form tests", "Valid account created; invalid attempts rejected.", "Not executed: Django init blocked by missing PyMySQL.", "Blocked"),
        ("T-02", "FR-03 / BR-04", "Attempt login for unverified and verified staff-role profiles.", "Auth integration", "Unverified denied; verified permitted.", "Not executed.", "Blocked"),
        ("T-03", "FR-06/07", "Submit valid report and inspect database fields.", "Django client + DB", "One pending report stores submitted values.", "Not executed.", "Blocked"),
        ("T-04", "FR-07", "Omit each required report field.", "Django client", "Validation message; no report created.", "Not executed.", "Blocked"),
        ("T-05", "FR-08", "Try allowed file, disallowed extension, and file >10 MB.", "Upload tests", "Allowed file saved; rejected upload not attached; warning shown.", "Not executed.", "Blocked"),
        ("T-06", "FR-09 / NFR-02", "User B requests User A report detail.", "Authorization test", "Access denied / not found.", "Not executed; authorization needs review.", "Blocked"),
        ("T-07", "FR-10 to FR-12", "Test report actions as admin, counselor, security, student.", "Role matrix tests", "Only authorized actions succeed.", "Not executed.", "Blocked"),
        ("T-08", "FR-13", "Create support thread and send messages as owner/responder.", "Django client + DB", "Messages persist under correct thread and sender.", "Not executed.", "Blocked"),
        ("T-09", "FR-14", "Upload recording and request it as unrelated student.", "Upload/authorization tests", "File/metadata stored; unrelated user denied.", "Not executed.", "Blocked"),
        ("T-10", "FR-16 / BR-03 / BR-08", "Mock panic POST with/without coordinates and SMS statuses 201/500/timeout.", "Mocked integration", "Critical report persists; recipients filtered; errors do not erase report.", "Not executed.", "Blocked"),
        ("T-11", "NFR-01 / NFR-03", "Inspect session protection and stored password representation.", "Security test/review", "Unauthenticated restricted routes denied; password hashed.", "Not executed.", "Blocked"),
        ("T-12", "NFR-06", "Run report, support, and panic browser flows in supported browsers.", "Manual compatibility", "No blocking UI defects; redirect and request behavior recorded.", "Not executed.", "Blocked")
    ]
    add_table(doc, ["Test ID", "Requirement / rule", "Scenario", "Type", "Expected result", "Actual result", "Status"], test_rows, font_size=6.9)
    heading(doc, "Non-Functional and Security Verification", 2)
    add_bullets(doc, [
        "Before release, run Django checks after installing the supported database driver and configuring the intended test database.",
        "Run static analysis and dependency/security checks; review all credentials and rotate any that have been exposed.",
        "Test role and object-level access for reports, evidence files, chats, recordings, and admin actions.",
        "Verify file size, extension, MIME/content signature, storage permissions, download authorization, and path handling.",
        "Test SMS/email failures with mocks and confirm sensitive narratives are not exposed in notification messages or logs.",
        "Use synthetic reports and participants for screenshots and demonstrations."
    ])

    heading(doc, "SYSTEM SETUP AND OPERATION")
    add_para(doc, "This is a development setup outline, not a production deployment guide. Use the actual project environment and a non-production database. The configured database is MySQL; the presence of `db.sqlite3` does not mean Django currently uses it.")
    heading(doc, "Prerequisites", 2)
    add_bullets(doc, [
        "Python 3.13 environment (the supplied project virtual environment is Python 3.13.2).",
        "Django 6.0.6 and application dependencies, including a supported MySQL driver.",
        "MySQL server and a database/user configured for the application.",
        "Optional test credentials for EmailJS and BulkSMS, kept outside source control."
    ])
    heading(doc, "Development Commands", 2)
    add_mermaid(doc, "Commands (Windows PowerShell)", r"""
# Open PowerShell in the SafeCampus_GBV project directory
.\venv\Scripts\Activate.ps1

# Install dependencies from a project requirements file after it is created
python -m pip install -r requirements.txt

# Configure DB, Django secret, email, and SMS values outside source control
# Then apply migrations and create an administrator
python manage.py migrate
python manage.py createsuperuser
python manage.py check
python manage.py test
python manage.py runserver
""", "The repository currently has no dependency manifest and the check failed because PyMySQL is absent; these commands require setup remediation first.")
    add_para(doc, "Do not use the committed/development database settings for production. Configure secret values securely and avoid copying credentials into terminal transcripts, screenshots, or the report.")

    heading(doc, "SOLUTION EVALUATION")
    add_para(doc, "The implementation contains a broad set of workflows aligned with the project purpose. The most complete data-modelled flows are reports, user profiles, support threads/messages, resources, and session recordings. Operational readiness is not established because the project could not complete its Django startup check, automated tests are absent, external delivery is unverified, and security gaps remain.")
    add_table(doc, ["Success criterion", "Current outcome", "Evidence"], [
        ("SC-01 Report submission/tracking", "Implemented in source; not verified at runtime.", "Views/templates/models inspected; automated test not run."),
        ("SC-02 Role-based case handling", "Role pages and admin decorators exist; object-level authorization needs remediation.", "Source inspection; role tests not run."),
        ("SC-03 Support conversations", "Thread and message data structures/views exist; not verified end-to-end.", "Source inspection; tests not run."),
        ("SC-04 Panic alert resilience", "Report and SMS attempt code exists; front-end navigation race means delivery is not assured.", "Source inspection; provider tests not run."),
        ("SC-05 Checks and tests", "Not met / blocked.", "Django check fails due to missing PyMySQL; tests.py is a placeholder.")
    ])
    add_para(doc, "Overall assessment: suitable as a development prototype after dependency configuration, but not ready for deployment with sensitive real-world GBV data until the security, privacy, authorization, file-storage, and emergency-delivery issues are resolved and independently tested.")

    heading(doc, "REFERENCES")
    references = [
        "Django Software Foundation. Django documentation: Authentication. https://docs.djangoproject.com/en/6.0/topics/auth/",
        "Django Software Foundation. Django documentation: Security. https://docs.djangoproject.com/en/6.0/topics/security/",
        "Django Software Foundation. Django deployment checklist. https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/",
        "Django Software Foundation. Django documentation: Managing files. https://docs.djangoproject.com/en/6.0/topics/files/",
        "Mermaid. Mermaid documentation: Syntax reference. https://mermaid.js.org/intro/",
        "BulkSMS. BulkSMS API documentation. https://www.bulksms.com/developer/",
        "Project source reviewed: SafeCampus_GBV/dashboard/models.py, dashboard/views.py, dashboard/urls.py, dashboard/emails.py, gbv_system/settings.py, and templates/."
    ]
    for ref in references:
        add_para(doc, ref, "List Number")
    add_para(doc, f"Source-code and template review date: {DATE}. No external stakeholder evidence or production operational records were supplied.")

    heading(doc, "APPENDICES")
    heading(doc, "Appendix A: Completion Checklist", 2)
    add_table(doc, ["Before final academic submission", "Status"], [
        ("Replace student name and student number on cover.", "Required"),
        ("Confirm whether SafeCampus is an approved real deployment or academic prototype.", "Required"),
        ("Add stakeholder/interview/observation evidence and approved sources.", "Required if claimed in problem analysis"),
        ("Insert genuine redacted screenshots for login, core report, admin/responder, validation, and completion states.", "Required by template"),
        ("Install missing dependencies, configure test database, run check and test suites, and fill actual results.", "Required"),
        ("Rotate hardcoded credentials and document only safe configuration.", "Required before sharing/deployment"),
        ("Review role/object-level access, anonymous-report wording, uploads, and panic delivery before real use.", "Required before production")
    ])
    heading(doc, "Appendix B: Repository and Deployment References", 2)
    add_para(doc, "Repository path reviewed: SafeCampus_GBV project directory supplied in the working environment. No GitHub repository URL or deployed system URL was supplied; insert them only if they exist and are approved for disclosure.")
    heading(doc, "Appendix C: Mermaid Diagram Sources", 2)
    add_para(doc, "The design sections above include Mermaid source for the context, use-case, architecture, ERD, activity, sequence, state, and class diagrams. Copy each source block into a Mermaid-compatible editor to render it. The diagrams describe observed implementation and explicitly note incomplete delivery and access-control behavior.")

    doc.core_properties.title = "SafeCampus GBV System - Final Project Report"
    doc.core_properties.subject = "NPRJ740 software development project"
    doc.core_properties.author = "Student Name - replace before submission"
    doc.core_properties.keywords = "SafeCampus, GBV, Django, project report"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
