from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted

OUT = Path("output/pdf/commercial_smart_facility_sustainability_manager_build_record.pdf")
OUT.parent.mkdir(parents=True, exist_ok=True)
NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#2463A8")
TEAL = colors.HexColor("#0F766E")
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#627081")
PALE = colors.HexColor("#F3F6F8")
LIGHT_TEAL = colors.HexColor("#E6F6F3")

s = getSampleStyleSheet()
s.add(ParagraphStyle(name="Cover", parent=s["Title"], fontName="Helvetica-Bold", fontSize=25, leading=31, textColor=colors.white, alignment=1, spaceAfter=12))
s.add(ParagraphStyle(name="Sub", parent=s["Normal"], fontName="Helvetica", fontSize=12, leading=17, textColor=colors.HexColor("#D9E2EC"), alignment=1))
s.add(ParagraphStyle(name="H1x", parent=s["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=NAVY, spaceAfter=9))
s.add(ParagraphStyle(name="H2x", parent=s["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=BLUE, spaceBefore=7, spaceAfter=4))
s.add(ParagraphStyle(name="Bodyx", parent=s["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=5))
s.add(ParagraphStyle(name="Smallx", parent=s["BodyText"], fontName="Helvetica", fontSize=8.3, leading=11, textColor=MUTED, spaceAfter=3))
s.add(ParagraphStyle(name="Bulletx", parent=s["BodyText"], fontName="Helvetica", fontSize=9.3, leading=13, leftIndent=13, firstLineIndent=-8, textColor=INK, spaceAfter=3))
s.add(ParagraphStyle(name="CodeX", parent=s["Code"], fontName="Courier", fontSize=7.7, leading=10.5, textColor=INK, backColor=PALE, borderPadding=7, spaceAfter=7))
s.add(ParagraphStyle(name="Callout", parent=s["BodyText"], fontName="Helvetica-Bold", fontSize=9.8, leading=13.5, textColor=NAVY, backColor=LIGHT_TEAL, borderPadding=7, spaceAfter=7))

def P(text, style="Bodyx"):
    return Paragraph(text, s[style])

def B(text):
    return P("- " + text, "Bulletx")

def C(text):
    return Preformatted(text.strip(), s["CodeX"])

def T(rows, widths):
    t = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#D9E2EC")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")]))
    return t

def hf(c, doc):
    c.saveState()
    if doc.page == 1:
        c.setFillColor(NAVY)
        c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.rect(0, 0, 5 * mm, A4[1], fill=1, stroke=0)
    else:
        c.setFillColor(NAVY); c.rect(0, A4[1]-8*mm, A4[0], 8*mm, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 7.5)
        c.drawString(16*mm, A4[1]-5.5*mm, "Commercial Smart Facility & Sustainability Manager")
    c.setFillColor(colors.HexColor("#D9E2EC") if doc.page == 1 else MUTED); c.setFont("Helvetica", 7.5)
    c.drawString(16*mm, 8*mm, "Rohit Limaye | PRN 1262240087")
    c.drawRightString(A4[0]-16*mm, 8*mm, str(doc.page))
    c.restoreState()

doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=17*mm, bottomMargin=15*mm, title="Commercial Smart Facility & Sustainability Manager - AI Build Record", author="Rohit Limaye")
doc.addPageTemplates([PageTemplate(id="main", frames=[Frame(doc.leftMargin, doc.bottomMargin+2*mm, doc.width, doc.height-2*mm, id="f")], onPage=hf)])
story = []

story += [Spacer(1,43*mm), P("COMMERCIAL SMART FACILITY", "Sub"), Spacer(1,4*mm), P("Commercial Smart Facility<br/>&amp; Sustainability Manager", "Cover"), P("AI prompt, workflow, architecture, and implementation record", "Sub"), Spacer(1,30*mm), P("Made by Rohit Limaye", "Sub"), P("PRN: 1262240087", "Sub"), PageBreak()]

story += [P("1. Purpose and prompt inventory","H1x"), P("This record documents the user-provided prompts, the decisions they produced, the run instructions, and the resulting prototype. It records the observable build process and does not reproduce private runtime policies or hidden platform instructions.","Callout"), P("Prompt A - airport adaptation and ML ideas","H2x"), C("""I want to do this project for airports. What all additional parameters could be used
Give me ideas and workflows alongside ML models that can be used to estimate the future."""),
P("Meaning","H2x"), P("Adapt the commercial facility concept to an airport setting. Identify useful parameters, operational workflows, and models for future water demand, hygiene demand, leaks, and maintenance risk.","Bodyx"), P("Prompt B - first simple airport scope","H2x"), C("""Lets create a simple project first
The airport will have 10 washrooms, each having the sensors listed below."""),
P("Meaning","H2x"), P("Start with a small, uniform prototype and make the first end-to-end workflow work before adding broader airport systems.","Bodyx"), PageBreak()]

story += [P("2. Scope and output requirements","H1x"), P("Prompt C - sensor parameters and outputs","H2x"), C("""We'll use parameters to gather data
Water & fixtures - Flow rate, pressure, flush counts, tap activations, urinal use, water tank levels
Hygiene - Soap/sanitizer/paper-towel levels, bin fill level, odor/VOC, humidity, last-cleaned time
Sustainability - Indoor temperature, CO2 levels
Our output will be
i) Continuous leak detection: flag a fixture when low-but-persistent flow continues
ii) Cleaning-before-complaint prediction: predict whether each restroom will need service in the next 30–60 minutes
iii) Water-demand forecast: estimate usage over the next day/week"""),
P("Meaning","H2x"), P("The data model contains water, fixture, hygiene, consumable, and indoor-environment signals. The analytics must produce persistent leak alerts, near-term cleaning risk, and demand forecasts.","Bodyx"), P("Prompt D - synthetic data and dashboard actions","H2x"), C("""Now I don't have real IOT sensors to work with so we'll have to generate artificial data, some it having regular usage patterns and anamolies too.
We'll create a dashboard with simple outputs like
High leak probability -> technician ticket immediately.
Hygiene breach predicted within 30 minutes -> cleaning ticket, prioritized by passenger volume and restroom criticality.
Refill predicted within shift -> add to cleaner route.
How should we go about developing this"""), P("Meaning","H2x"), P("Use a reproducible simulator instead of waiting for hardware. Generate regular time-of-day demand and sustained anomaly windows, then connect predictions to actions.","Bodyx"), PageBreak()]

story += [P("3. Simplification and implementation","H1x"), P("Prompt E - remove unnecessary airport dimensions","H2x"), C("""Lets not make it complicated by adding terminal zones, arrivals, departures, food court, gates, staff area
You give me generated data over the last 3 months for every 5 mins for each attribute in the washroom
Generate all the files necessary for the project and lets starting implementing it"""), P("Meaning","H2x"), P("Keep all washrooms in one simple population. Do not add terminal geography or flight-operation joins. Generate 90 days of five-minute data for each washroom and begin implementation.","Bodyx"), P("Resulting design decisions","H2x"), B("Ten washrooms are represented as R001 through R010."), B("The simulator emits 25,920 intervals per washroom, or 259,200 total rows."), B("Daily curves include low overnight use and recurring demand peaks."), B("Anomalies are sustained intervals: leaks, missed cleaning, and low consumables."), B("A static browser dashboard uses JSON outputs and Python's HTTP server."), P("Implementation sequence","H2x"), C("""1. Generate a reproducible synthetic history.
2. Create leak, cleaning, refill, and water-demand features.
3. Split, train, test, and score the models.
4. Create tickets from high-confidence conditions.
5. Export dashboard JSON and a seven-day forecast.
6. Demonstrate live playback with held-out test data."""),
PageBreak()]

story += [P("4. Run instructions and meanings","H1x"), P("The following commands are the project-level instructions supplied for Windows PowerShell.","Bodyx"), T([[P("Command","Smallx"),P("Meaning","Smallx")],[P("cd \"C:/Users/Rohit/Documents/Codex/2026-09-15/i-want-to-do-this-project\"","CodeX"),P("Move PowerShell into the project directory so relative paths resolve correctly.","Bodyx")],[P("python -m pip install -r requirements.txt","CodeX"),P("Install NumPy, Pandas, Scikit-learn, and Joblib.","Bodyx")],[P("python generate_data.py","CodeX"),P("Create the three-month, five-minute synthetic sensor history.","Bodyx")],[P("python run_pipeline.py","CodeX"),P("Split the data, train and test models, create forecasts, and export dashboard and live-feed files.","Bodyx")]], [82*mm,89*mm]), P("Dashboard serving command","H2x"), C("""python -m http.server 8000
# Open http://localhost:8000/dashboard/"""), P("This serves the static dashboard locally. It loads dashboard_data.json, live_test_stream.json, and live_models.json from outputs.","Bodyx"), PageBreak()]

story += [P("5. Synthetic data workflow","H1x"), P("The simulator creates a simple digital twin of 10 washrooms. A fixed random seed makes the dataset reproducible.","Bodyx"), T([[P("Group","Smallx"),P("Generated fields","Smallx"),P("Purpose","Smallx")],[P("Water and fixtures","Smallx"),P("Flow, expected flow, pressure, flushes, taps, urinal use, tank level","Smallx"),P("Measure demand and identify excess flow.","Smallx")],[P("Hygiene","Smallx"),P("Soap, sanitizer, paper towels, bin fill, odor/VOC, humidity, last cleaned","Smallx"),P("Estimate service and replenishment need.","Smallx")],[P("Sustainability","Smallx"),P("Temperature and CO2","Smallx"),P("Provide environmental context.","Smallx")],[P("Context","Smallx"),P("Passenger volume, criticality, timestamps, anomaly labels","Smallx"),P("Support prioritization and evaluation.","Smallx")]], [34*mm,79*mm,58*mm]), P("Anomaly injection","H2x"), B("Leak events add low persistent flow and a related pressure change."), B("Missed-cleaning events let bin fill, odor, humidity, and cleaning debt rise."), B("Consumable events keep soap and paper levels low long enough to trigger refill risk."), B("The final history contains demonstrable incidents for the dashboard."), P("Every row is one washroom at one timestamp. The five-minute grain is preserved for training, testing, playback, and auditability.","Callout"), PageBreak()]

story += [P("6. Model and evaluation workflow","H1x"), P("The first 80% of each washroom timeline trains the models. The final 20% remains held out for evaluation and random live playback.","Callout"), T([[P("Component","Smallx"),P("Approach","Smallx"),P("Output","Smallx")],[P("Leak detection","Smallx"),P("Rules over excess flow, persistence, and pressure","Smallx"),P("Leak probability and technician ticket","Smallx")],[P("Cleaning prediction","Smallx"),P("Logistic regression trained on 80%","Smallx"),P("Hygiene breach probability in 30 minutes","Smallx")],[P("Water forecast","Smallx"),P("Ridge regression with time, weekday, washroom, and expected passengers","Smallx"),P("Five-minute demand and day/week totals","Smallx")]], [38*mm,83*mm,50*mm]), P("Split procedure","H2x"), C("""For each restroom:
  first 80% chronological rows -> training_data.csv
  final 20% chronological rows  -> test_data.csv

Train models only on training_data.csv.
Evaluate cleaning predictions on test_data.csv.
Use held-out test_data.csv as the live sensor stream."""),
P("The reported metrics are synthetic-data metrics. They show that the pipeline runs and the labels are learnable. They are not production accuracy claims until real sensor history and confirmed outcomes exist.","Bodyx"), PageBreak()]

story += [P("7. Live sensor playback workflow","H1x"), P("The Play button turns the held-out partition into a controllable sensor broadcast. It demonstrates production interaction without physical IoT hardware.","Bodyx"), C("""Browser loads:
  dashboard_data.json       -> initial washroom view
  live_test_stream.json     -> held-out sensor records
  live_models.json          -> exported model coefficients

When Play is pressed:
  1. Choose a random held-out record.
  2. Display timestamp and sensor values.
  3. Recalculate leak, cleaning, refill, and water-use risk.
  4. Show a recommended action.
  5. Update the matching washroom row.
  6. Repeat approximately once per second until Pause."""),
P("Browser-side decisions","H2x"), B("Leak score combines persistent excess flow, current excess flow, and pressure."), B("Cleaning risk applies exported logistic-regression coefficients."), B("Refill risk checks the lowest consumable and within-shift flag."), B("Water prediction applies exported Ridge-regression parameters."), P("Random playback exposes the dashboard to different washrooms and conditions on every session. It is a demonstration stream, not a time-faithful replay.","Callout"), PageBreak()]

story += [P("8. Architecture and repository outputs","H1x"), T([[P("Layer","Smallx"),P("Implementation","Smallx")],[P("Source","Smallx"),P("src/simulator.py and generate_data.py create synthetic five-minute readings.","Smallx")],[P("Features","Smallx"),P("src/analytics.py derives excess flow, persistence, refill, cleaning, and forecast features.","Smallx")],[P("Models","Smallx"),P("Scikit-learn LogisticRegression and Ridge pipelines are persisted and exported to JSON.","Smallx")],[P("Orchestration","Smallx"),P("run_pipeline.py splits, trains, evaluates, forecasts, and writes artifacts.","Smallx")],[P("Presentation","Smallx"),P("dashboard/index.html loads JSON and runs the live playback.","Smallx")]], [38*mm,133*mm]), P("Main outputs","H2x"), C("""outputs/training_data.csv                 80% training partition
outputs/test_data.csv                     20% held-out partition
outputs/live_test_stream.json             browser test stream
outputs/live_models.json                  browser scoring parameters
outputs/dashboard_data.json               initial dashboard data
outputs/water_demand_forecast_7_days.csv  forecast output
outputs/model_metrics.json                evaluation output"""), PageBreak()]

story += [P("9. Operational outputs and validation","H1x"), T([[P("Condition","Smallx"),P("Dashboard action","Smallx")],[P("High leak probability","Smallx"),P("Immediate technician ticket with persistent-flow evidence.","Smallx")],[P("Cleaning risk above threshold","Smallx"),P("Cleaning ticket ranked using passenger volume and criticality.","Smallx")],[P("Consumable risk above threshold","Smallx"),P("Add the washroom to the cleaner's refill route.","Smallx")]], [62*mm,109*mm]), P("Validation performed","H2x"), B("Automated tests verify row counts, washroom coverage, held-out anomalies, split completeness, live stream size, and forecast coverage."), B("The PDF and dashboard artifacts are generated locally from reproducible scripts."), B("The final PDF is rendered to PNGs and checked for page count, clipping, and legibility."), P("Limitations and next steps","H2x"), B("Synthetic labels and metrics must be replaced with real maintenance and cleaning outcomes."), B("Random playback does not preserve event order. A production stream should use timestamps and transport ordering."), B("Future integrations can replace CSV with MQTT, REST, or a facilities-management platform."), P("The build follows a deliberately small path: simulate first, keep the 80/20 boundary explicit, make predictions explainable, connect predictions to tickets, and demonstrate the live loop through held-out test data.","Callout")]

doc.build(story)
print(OUT)
