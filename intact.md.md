INTACT – PUC1 Technical Meeting

Date: July 2026

Participants

K3Y, UBITECH, University of Lancaster, Siemens, TUC, THALES, MONTIMAGE (discussed), SBA (finance discussion)

1. PUC1 Integration Progress
K3Y / AVA Integration
A follow-up meeting was held with Alexandros (UBITECH) regarding the deployment of AVA within PUC1.
The deployment process and required modifications were presented.
K3Y is adapting its components to ensure compatibility with the PUC1 environment.
Updated Docker Compose and Helm charts are expected next week.
Updated deployment packages will then be provided to UBITECH for deployment.

Actions

Update Docker Compose and Helm charts.
Deliver updated deployment package to UBITECH.
Validate deployment within PUC1.
2. University of Lancaster Integration
A technical meeting was held with the University of Lancaster.
Lancaster has already provided the required integration information.
Current work focuses on connecting the K3Y component with Lancaster's tool.
Packaging and deployment are expected to be completed next week.

Actions

Complete integration with Lancaster tool.
Deploy on UBITECH infrastructure.
Verify successful message exchange.
3. MONTIMAGE Integration
Integration of the MMT probes is still pending.
Timing depends on MONTIMAGE availability.
There is concern that summer holidays may delay this activity.

Target

Complete integration before the end of July if possible.
4. Deployment Architecture

The deployment demonstrated during previous meetings:

Docker Compose deployment
Kubernetes deployment still under preparation
Sidecar deployment approach remains under investigation.

The intention is to deploy Cyber Probe containers alongside the UPF using a sidecar architecture.

5. Demo Scenario

The demonstrated attack scenario involves:

attacker targeting the SMF management interface
deletion or flooding of network sessions
IDS/probes monitoring abnormal behaviour.

An open question remains whether the current version of the UBITECH 5G Core still allows these attacks.

Action

Verify compatibility between the current 5G Core release and the attack scenarios.
6. Cyber Range (WP4)

Discussion followed yesterday's WP4 meeting.

Current understanding:

Cyber Range will be deployed inside the PUC1 environment.
It will replicate the UBITECH infrastructure:
Dashboard
AVA
Kubernetes environment
Virtual machines

Current blocker:

THALES has not yet assigned a dedicated developer.

No additional support from partners is currently required.

7. Financial Reporting (P1)

Partners requested to finalise responses regarding the suspended payment letter.

Partners concerned:

SBA
TUC
K3Y

Objective:

submit updated explanations
finalise P1 claims
unblock project payments.
8. Upcoming Meetings

There was clarification regarding the upcoming meetings.

Technical Meeting
8 September
Online
Chaired by Bruno
General Assembly
6–7 October
In person
Hosted by Demokritos in Athens

Discussion also included the possibility of extending the October meeting with an additional technical workshop if needed.

9. Actions
Action	Responsible	Due
Update Docker Compose and Helm charts	K3Y	Next week
Send updated deployment package to UBITECH	K3Y	Next week
Validate deployment in PUC1	UBITECH & K3Y	Next week
Verify communication between components	K3Y / Lancaster	Next week
Complete Lancaster integration	K3Y	End of July
Contact MONTIMAGE regarding MMT probes	K3Y / UBITECH	TBD
Verify compatibility of demo attacks with current 5G Core	UBITECH	TBD
Assign Cyber Range developer	THALES	TBD
Submit updated financial explanations	SBA, TUC, K3Y	ASAP
Organise WP leaders meeting	Despoina	End of month
Send clarification email regarding September and October meetings	Despoina	ASAP
Main risks identified
Possible delays due to summer holidays (especially August).
MONTIMAGE integration may slip if resources are unavailable.
Cyber Range development currently lacks a dedicated developer.
Compatibility issues may arise if the latest 5G Core version no longer supports the planned attack scenarios.
Remaining financial clarifications must be completed to avoid further delays in project payments.


======================
e Meet Meeting
Summary
Scratchpad
Meeting Setup
Two agenda areastechnical updates and project management
Focus on aligning tasks 3.2 and 3.3 between QNR and Mellytek
Mellytek joining late; team may have internal delays
Technical Updates
Early-stage updates on automate gap analysis engine
Preliminary notes on Compliance Control Center
Ioannes Pastelas leading development for both modules
Reviewing operational workflow and current technology stack
Document Processing Pipeline
PDF input requires parsing pipeline for document processing
Pipeline splits documents into relevant chunks
Extracts metadata, citations, and summaries for structured output
Requirements extracted from documents as key output
Task 3.4agents extract status from processed documents
Compliance & Standards
Need to develop compliance modules for organizational use
Plan to add European compliance module integration
Compliance Requirements Matching
Phase determines which reporting requirements apply to organization
Rule-based matching using user profile (e.g., H3L domain)
FutureLLM-based reasoning for general-purpose intelligence
Next Steps & Task 3.1
Provide more detail on user profiling and obligations matching
Task 3.1 details to be covered in next meetings
Compliance Command Center UI shown with gap analysis screenshots
Compliance Command Center Development
Phase 1compliance assessment phase to be demonstrated
Phase 2compliance engine implementation planned
Phase 3decision-making profile for compliance
Process tracks compliance status per entity with remediation tasks
Meeting Logistics & Slide Sharing
Slides will be uploaded to DeTangle Work Package 3 folder
Folder organized by upcoming meeting date
Current meeting slides copied to next meeting's folder
Partners can use previous slides as source material
Development Status Check
AskAny internal blockers or cross-workpackage questions?
No technical blockers reported; collaboration scope discussed
Mellytek invited to bring additional members for broader Q&A
Use Case Alignment Discussion
Challenge identifiedaligning use cases across partners
Inputbinary file representing software component for certification check
Outputoverall assessment report on certification status
Risk profile included as part of the assessment output
JSON format proposed for input/output data exchange
CycloneDX referenced as potential component data source
Use Case Alignment Discussion (cont.)
AskQNR to show use cases for alignment discussion
Use cases may be created as separate deliverables
Goalimprove QNR deliverable quality through alignment
Task 3.2 & 3.3 Technical Development
Profiling stagetwo routes — CRA accreditation and CRA compliance
Two routesCRA compliance orgs vs MSA/accreditation auditors
Defining workflows per route for questionnaires and analysis
Input requirements still being finalized; no binary files needed
Plan to use Mellytek's CRA use case as template for project
Set up meeting with iChem for MSA workflow input
iChem is only partner fitting MSA/accreditation workflow
Next stepmeeting with all WP3 partners on 3.2/3.3 alignment
Task 3.2 & 3.3 Integration
Proposaluse 3.2 modules as input for 3.3 modules
Modules designed to accept 3.2 input for analysis tasks
Tool goes beyond questionnaires; integrates external data sources
3.2 assessment/risk report feeds into 3.3 accreditation workflow
Team & Communication
Open QWhether Detangle and Crackowi teams share members
Deadlines and business travel may delay responses
Architecture & Alignment Requests
QNR to share detailed tool architecture and module descriptions
Architecture info needed to map output integration points
Alignment loop closure requires cross-team coordination
Task 3.3 Workflow Planning
AskMellytek to provide serial workflow diagrams for 3.3
Goalmap step-by-step progression (steps 1-4) for accreditation
Current development still early; diagrams to guide planning
Decisionhold non-core features; focus on core first
Staged approachadd extra features in next iteration
Deliverables & Amendment
Decisionreduce number of deliverables; no objections raised
Initiate amendment request in next days
Deliverables still required for Work Packages 3 and 4
Partner Response Review
Reviewing partner's response to earlier comments sent
Response appears generic; does not address specific questions
Open QWhether partner actually read the detailed input shared
Partner Response Review (cont.)
Three emails sent to partner via cloud platform
Partner's version includes body text but not retitling
Open QPartner's opinion on D4P and effort concerns
Concern raised58 weeks tight for WP3 plus pilot implementation
Pilot One has 25 separate PMs distinct from Turku's WP3
Send mail to partner clarifying pilot PMs vs WP3 scope
Partner Response Follow-Up
Response not entirely negative; no hard rejection received
Three emails sentcomments reply, schedule, and third pending
Send partner email clarifying Pilot 1 PMs; Despoina to review draft
Proposal & Document Updates
Send partner latest proposal version; confirm 64 PMs accepted
AskRequest partner to use latest proposal edition
AskDoes partner believe 64 PMs are dedicated to Pilot 1/2? (likely yes)
U2 has extra 25 PMs separate from the 64
Proposal Finalization
Decisionshare latest proposal version with partner now
Upload proposal online, then copy-paste partner edits Friday
Pilot PM Allocation Analysis
Partner has only 3 PMs across both validation work packages
3 PMs insufficient if running pilot alongside Turku
Partner's own pilot text supports clean reading interpretation
Riskloose wording may mask misaligned PM expectations
Despoina to send partner email clarifying U2 has 25 extra PMs
Proposal Document & PM Clarification
Google Docs version is the working document for effort allocation
University of Turku is parent beneficiary with 25 PMs as owner
Current allocation spans WP7 and WP8 (two validation work packages)
Outstanding Deliverables & Follow-Ups
BlockerSaracino has not sent OCD; one month overdue
Follow up with Saracino on OCD delivery
Send OCD to University of Turku as well
Email & Document Coordination
Send latest proposal version to partner; CC Despoina
Pilot One Text & Budget Discussion
AskConfirm Pilot One text consistency with Turku's contribution
Open QWhether tight allocation reflects workload or budget constraints
Decisionadopt text changes; remove all other edits from proposal
Decisionupload latest proposal version to shared link
Notify partners to use new link; old edits won't be tracked
Proposal Version Management
Decisionoverwrite old link with latest version, not two versions
Check if partners added edits to old link before overwriting
Decisioncreate new file/link, not rename; rename keeps same URL
Riskold link persists; partners may still access outdated version
Despoina creating new file via Teams upload (in progress, done)
Proposal Version Management (cont.)
Riskpartner may blame version mismatch for any errors
Decisionpartner edits must be done offline, not online
Send partner latest version for offline editing; target Friday
Email partners: all edits go to new file only; old version backed up
Confirmedall partners have edit access to new file; same permissions as old
Proposal Formatting & References
Send reference list to Despoina for proposal formatting
Cross-references added as hyperlinks in proposal text
Reference & Feedback Management
Upload reference files to cloud; two feedback items pending
Open QWhether feedback from Hlias has been uploaded to cloud
Ethics & Budget Review
Site needs formatting improvements; layout not user-friendly
EU form structure described as complex and chaotic
Budget section has changes to review
Open QWhether project involves personal data, embryos, or human participants
Clinical pilot processes health data; border customs may involve personal data
Open QWhich Part B page to reference; unclear which page covers pilots
Riskapproaching deadline makes online submission harder; may change later
Send ethics questions to partner via copy-paste for context (sent)
Ethics & Data Export Questions
Decisionpersonal data export from EU confirmed as no
Online Submission & Document Finalization
Navigating to online version of ethics form for submission
Open QWhether all changes are finalized in current version
Open QWhether Despoina completed all text changes across sections
Comment flagged"Trafficon" named but missing from current version
Trafficon may be affiliate identity; awaiting Turku confirmation tomorrow
Decisionleave Trafficon comment open; update after Turku reply tomorrow
Budget & Subcontracting Review
Two tables require payment if subcontracting exceeds 15%
Review budget tables tomorrow after Turku reply
Proposal expected to score well after tool-suggested changes
Proposal Review & Comments
Despoina reviewing comments in proposal document for context
Checking original version to provide context for replies
Decisionreply to evaluation comment; all changes done except Trafficon
Reply to evaluation comment noting new version being shared
Proposal Finalization & Next Steps
Riskreviewer may re-run tool; changes must be finalized before submission
Submit proposal to Fabl for final review
Decisionpause edits; wait for Aero's response before further changes
Proposal Scoring & Wrap-Up
Score dropped to 3.75; cause unknown
Despoina to add citations to proposal
Monitor Aero's email response for next steps
Listening
