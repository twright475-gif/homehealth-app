from fastapi import FastAPI, Form
from database import engine, SessionLocal
from models import Base, Visit
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import pandas as pd

app = FastAPI()

# This creates the visits table in SQLite
Base.metadata.create_all(bind=engine)

# Login page
@app.get("/", response_class=HTMLResponse)
def login_page(msg: str = ""):
    html = ""
    if msg:
        html += f"<p style='color: red; font-weight: bold;'>{msg}</p>"
    html += """
    <h2>Login</h2>
    <form action="/login" method="post">
        name: <input name="name"><br><br>
        Role:
        <select name="role">
            <option value="nurse">Nurse</option>
            <option value="admin">Admin</option>
        </select><br><br>
        <button type="submit">Enter</button>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/login")
def login_submit(name: str = Form(...), role: str = Form(...)):
    if role == "nurse":
        return RedirectResponse(url="/?msg=Welcome+Nurse+" + name + "!", status_code=303)
    elif role == "admin":
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return RedirectResponse(url="/login?msg=Invalid+role", status_code=303)

@app.get("/nurse", response_class=HTMLResponse)
def form(msg: str = ""):  # add optional msg parameter
    html = ""
    if msg:
        html += f"<p style='color: green; font-weight: bold;'>{msg}</p>"

    html += """
    <h2>Submit Visit</h2>
    <form action="/submit" method="post">
        Nurse Name: <input name="nurse"><br><br>
        Patient Name: <input name="patient"><br><br>
        Date: <input name="date"><br><br>
        Hours: <input name="hours"><br><br>
        Mileage: <input name="mileage"><br><br>
        Notes: <input name="notes"><br><br>
        <button type="submit">Submit</button>
    </form>
    """
    return HTMLResponse(content=html)


@app.post("/submit")
def submit_visit(
    nurse: str = Form(...),
    patient: str = Form(...),
    date: str = Form(...),
    hours: float = Form(...),
    mileage: float = Form(...),
    notes: str = Form(...)
):
    db = SessionLocal()

    new_visit = Visit(
        nurse_name=nurse,
        patient_name=patient,
        date=date,
        hours=hours,
        mileage=mileage,
        notes=notes
    )

    db.add(new_visit)
    db.commit()
    db.close()

    # Redirects back to blank submission form
    return RedirectResponse(url="/?msg=Visit+submitted+successfully!", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    db = SessionLocal()
    visits = db.query(Visit).all()
    db.close()

    # Build HTML table
    html = "<h2>All Visits</h2>"
    html += "<table border='1' style='border-collapse: collapse;'>"
    html += "<tr><th>ID</th><th>Nurse</th><th>Patient</th><th>Date</th><th>Hours</th><th>Mileage</th><th>Notes</th><th>Approved</th></tr>"

    for v in visits:
        html += f"<tr>"
        html += f"<td>{v.id}</td>"
        html += f"<td>{v.nurse_name}</td>"
        html += f"<td>{v.patient_name}</td>"
        html += f"<td>{v.date}</td>"
        html += f"<td>{v.hours}</td>"
        html += f"<td>{v.mileage}</td>"
        html += f"<td>{v.notes}</td>"
        html += f"<td>{v.approved}</td>"

    # Add Approve button if not approved
        if not v.approved:
            html += f"<td><form method='post' action='/approve/{v.id}'>"
            html += f"<button type='submit'>Approve</button>"
            html += f"</form></td>"
        else:
            html += f"<td>Approved</td>"

        html += f"</tr>"

    html += "</table>"
    return html




@app.post("/approve/{visit_id}")
def approve_visit(visit_id: int):
    db = SessionLocal()
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if visit:
        visit.approved = True  # mark visit as approved in DB
        db.commit()

        # Log approved visit to Excel
        try:
            df = pd.read_excel("approved_visits.xlsx")
        except FileNotFoundError:
            df = pd.DataFrame(columns=["ID","Nurse","Patient","Date","Hours","Mileage","Notes","Approved At"])

        df = pd.concat([df, pd.DataFrame([{
            "ID": visit.id,
            "Nurse": visit.nurse_name,
            "Patient": visit.patient_name,
            "Date": visit.date,
            "Hours": visit.hours,
            "Mileage": visit.mileage,
            "Notes": visit.notes,
            "Approved At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])], ignore_index=True)

        df.to_excel("approved_visits.xlsx", index=False)

    db.close()
    return RedirectResponse(url="/admin", status_code=303)
    