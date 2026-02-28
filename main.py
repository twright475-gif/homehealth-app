from fileinput import filename
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
/* Global Body */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f0f4f8;
    margin: 0;
    padding: 0;
}

/* Container Card */
.card {
    background: #ffffff;
    margin: 40px auto;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 6px 15px rgba(0,0,0,0.1);
    max-width: 850px;
}

/* Headings */
h2 {
    color: #1f4e79;
    text-align: center;
    margin-bottom: 20px;
}

/* Forms */
form {
    display: flex;
    flex-direction: column;
}

input, select, textarea {
    width: 100%;
    padding: 10px;
    margin-bottom: 15px;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 1rem;
}

textarea {
    resize: vertical;
}

/* Buttons */
button {
    background-color: #1f4e79;
    color: #fff;
    font-weight: bold;
    padding: 12px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: 0.3s;
}

button:hover {
    background-color: #163a5f;
}

/* Success/Error messages */
.success {
    color: green;
    font-weight: bold;
    text-align: center;
    margin-bottom: 15px;
}

.error {
    color: red;
    font-weight: bold;
    text-align: center;
    margin-bottom: 15px;
}

/* Admin Table */
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    box-shadow: 0 6px 15px rgba(0,0,0,0.05);
    background: #ffffff;
}

th, td {
    padding: 12px;
    text-align: center;
}

th {
    background-color: #1f4e79;
    color: #ffffff;
}

tr:nth-child(even) {
    background-color: #f8faff;
}

tr:hover {
    background-color: #e3f2fd;
}

.action-form {
    margin: 0;
}

.download-button {
    margin-top: 20px;
    display: block;
    width: 220px;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
}
</style>
"""

# This creates the visits table in SQLite
Base.metadata.create_all(bind=engine)

# Login page
@app.get("/", response_class=HTMLResponse)
def login_page(msg: str = ""):
    html = f"""
    <html>
    <head>{STYLE}</head>
    <body>
    <div style="display:flex; justify-content:center; align-items:center; min-height:100vh;">
    <div class="card">
    <h2>Login</h2>
    """
    if msg:
        html += f"<p class='error'>{msg}</p>"
        
    html += """
    <form action="/login" method="post">
        Name: <input name="name" placeholder="Enter your name"><br>
        Role:
        <select name="role">
            <option value="nurse">Nurse</option>
            <option value="admin">Admin</option>
        </select><br>
        <button type="submit">Enter</button>
    </form>
    </div>
    </div>
    </body>
    </html>
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
    html = f"""
    <html>
    <head>{STYLE}</head>
    <body>
    <div style="display:flex; justify-content:center; align-items:center; min-height:100vh;">
    <div class="card">
    <h2>Submit Visit</h2>
    """
    if msg:
        html += f"<p class='success'>{msg}</p>"

    html += """
    <form action="/submit" method="post">
        Nurse Name: <input name="nurse" placeholder="Enter your name"><br>
        Patient Name: <input name="patient" placeholder="Enter patient name"><br>
        Date: <input name="date" type="date"><br>
        Hours: <input name="hours" type="number" step="0.1"><br>
        Mileage: <input name="mileage" type="number" step="0.1"><br>
        Notes: <textarea name="notes" placeholder="Optional notes"></textarea><br>
        <button type="submit">Submit</button>
    </form>
    </div>
    </div>
    """
    return HTMLResponse(content=html)

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    db = SessionLocal()
    visits = db.query(Visit).all()
    db.close()

    html = f"""
    <html>
    <head>{STYLE}</head>
    <body>
    <div style="padding:40px; max-width:1000px; margin:auto;">
    <h2 style="text-align:center;">Admin Dashboard</h2>
    <table>
      <tr>
        <th>ID</th>
        <th>Nurse</th>
        <th>Patient</th>
        <th>Date</th>
        <th>Hours</th>
        <th>Mileage</th>
        <th>Notes</th>
        <th>Status</th>
        <th>Action</th>
      </tr>
    """

    # Loop through visits to generate table rows
    for v in visits:
        html += "<tr>"
        html += f"<td>{v.id}</td>"
        html += f"<td>{v.nurse_name}</td>"
        html += f"<td>{v.patient_name}</td>"
        html += f"<td>{v.date}</td>"
        html += f"<td>{v.hours}</td>"
        html += f"<td>{v.mileage}</td>"
        html += f"<td>{v.notes}</td>"

        if v.approved:
            html += "<td>Approved</td>"
            html += "<td>—</td>"
        else:
            html += "<td>Pending</td>"
            html += f"""
            <td>
                <form class='action-form' method='post' action='/approve/{v.id}'>
                    <button type='submit'>Approve</button>
                </form>
            </td>
            """
        html += "</tr>"

    # Close table and add download button
    html += """
    </table>
    <div style="text-align:center; margin-top:20px;">
        <form class="download-button" action="/download-approved" method="get">
            <button type="submit">Download Approved Visits</button>
        </form>
    </div>
    </div>
    </body>
    </html>
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
    return RedirectResponse(url="/nurse?msg=Visit+submitted+successfully!", status_code=303)


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
import os

@app.get("/download-approved")
def download_approved():
    visits = SessionLocal().query(Visit).filter(Visit.approved == True).all()
    
    if not visits:
        return HTMLResponse(content="<p>No approved visits to download.</p>")
    
    # Create a new DataFrame from current approved visits
    new_df = pd.DataFrame([{
        "ID": v.id,
        "Nurse": v.nurse_name,
        "Patient": v.patient_name,
        "Date": v.date,
        "Hours": v.hours,
        "Mileage": v.mileage,
        "Notes": v.notes,
        "Approved At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    } for v in visits])

    filename = "approved_visits.xlsx"

    # Read existing file and append new data, if file exists
    if os.path.exists(filename):
        existing_df = pd.read_excel(filename)
        df_to_save = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df_to_save = new_df

    # Save/overwrite the persistent Excel file
    df_to_save.to_excel(filename, index=False)

    return FileResponse(
        filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )