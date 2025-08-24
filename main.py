from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
from fastapi.staticfiles import StaticFiles
from models import Job, Application, User
from auth import hash_password, verify_password

from starlette.middleware.sessions import SessionMiddleware




app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="supersecret")
templates = Jinja2Templates(directory="templates")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Homepage: list jobs
@app.get("/", response_class=HTMLResponse)
def read_jobs(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(models.Job).all()
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs})

# Create job form
@app.get("/jobs/create", response_class=HTMLResponse)
def create_job_form(request: Request):
    return templates.TemplateResponse("create_job.html", {"request": request})

@app.post("/jobs/create")
def create_job(title: str = Form(...), description: str = Form(...), company: str = Form(...), location: str = Form(...), db: Session = Depends(get_db)):
    job = models.Job(title=title, description=description, company=company, location=location)
    db.add(job)
    db.commit()
    return RedirectResponse("/", status_code=303)

# Job details + application form
@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@app.post("/jobs/{job_id}/apply")
def apply_job(job_id: int, name: str = Form(...), email: str = Form(...), resume: str = Form(...), db: Session = Depends(get_db)):
    application = models.Application(name=name, email=email, resume=resume, job_id=job_id)
    db.add(application)
    db.commit()
    return RedirectResponse(f"/jobs/{job_id}", status_code=303)

@app.get("/admin/login")
def admin_login_form(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid credentials"})

    request.session["admin"] = True
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

def require_admin(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse(url="/admin/login", status_code=303)


@app.get("/admin/dashboard")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("admin"):
        return RedirectResponse(url="/admin/login", status_code=303)

    jobs = db.query(Job).all()
    applications = db.query(Application).all()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "jobs": jobs,
        "applications": applications
    })
