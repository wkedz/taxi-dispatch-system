from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from common.logger import configure_root_logging, get_logger

configure_root_logging(service_name="grid")
log = get_logger(__name__)
log.info("Grid app booting")


app = FastAPI(title="Taxi Grid")
app.mount("/", StaticFiles(directory="./grid_service/app/static", html=True), name="static")
