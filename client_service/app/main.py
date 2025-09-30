from fastapi import FastAPI

from client_service.app.simulator import ClientSimulator
from common.logger import configure_root_logging, get_logger

configure_root_logging(service_name="client")
log = get_logger(__name__)
log.info("Client app booting")

simulator = ClientSimulator()

async def lifespan(app: FastAPI):
    await simulator.start()
    yield
    await simulator.stop()


app = FastAPI(title="Client Simulator", lifespan=lifespan)

