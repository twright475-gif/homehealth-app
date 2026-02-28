from fastapi import FastAPI, Form
from database import engine, SessionLocal
from models import Base, Visit
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import pandas as pd

app = FastAPI()

# Simple professional CSS styling
STYLE = """
<style>
body {
    font-family: Arial, sans-serif;
    background-color: #f4f6f9;
    margin: 40px;
}

h2 {
    color: #1f4e79;
}

form {
    background: white;
    padding: 20px;
    border-radius: 8px;
    width: 400px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
}

input, select {
    width: 100%;
    padding: 8px;
    margin-top: 5px;
    margin-bottom: 15px;
    border-radius: 4px;
    border: 1px solid #ccc;
}

button {
    background-color: #1f4e79;
    color: white;
    padding: 8px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover {
    background-color: #163a5f;
}

table {
    width: 100%;
    background: white;
    border-collapse: collapse;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
}

th {
    background-color: #1f4e79;
    color: white;
    padding: 10px;
}

td {
    padding: 8px;
    text-align: center;
}

tr:nth-child(even) {
    background-color: #f2f2f2;
}

.success {
    color: green;
    font-weight: bold;
}

.error {
    color: red;
    font-weight: bold;
}
</style>
"""

# This creates the visits table in SQLite
Base.metadata.create_all(bind=engine)

# Login page
@app.get("/", response_class=HTMLResponse)
def login_page(msg: str = ""):
    html = STYLE
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
        return RedirectResponse(url=f"/nurse?msg=Welcome+Nurse+{name}!", status_code=303)
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

    # Add Download button below the table
    html += """
    <br><br>
    <form action="/download-approved" method="get">
        <button type="submit">Download Approved Visits</button>
    </form>
    """
    
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
    

from fastapi.responses import FileResponse

@app.get("/download-approved")
def download_approved():
    db = SessionLocal()
    visits = db.query(Visit).filter(Visit.approved == True).all()
    db.close()

    db = pd.DataFrame([{
        "ID": v.id,
        "Nurse": v.nurse_name,
        "Patient": v.patient_name,
        "Date": v.date,
        "Hours": v.hours,
        "Mileage": v.mileage,
        "Notes": v.notes
    } for v in visits]) 

    filrname = "approved_visits.xlsx"
    db.to_excel(filename, index=False)

    return FileResponse(
        filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=filename
    )
    