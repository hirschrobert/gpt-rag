from fastapi.templating import Jinja2Templates
from ..paths import BASE_PATH
from ..models.Models import SessionLocal

templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
