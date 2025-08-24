from pydantic import BaseModel

class JobBase(BaseModel):
    title: str
    description: str
    company: str
    location: str

class JobCreate(JobBase):
    pass

class JobOut(JobBase):
    id: int
    class Config:
        orm_mode = True

class ApplicationBase(BaseModel):
    name: str
    email: str
    resume: str

class ApplicationCreate(ApplicationBase):
    pass
