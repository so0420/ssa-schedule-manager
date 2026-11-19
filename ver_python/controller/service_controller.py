from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


class ServiceController:

    def __init__(self, templates: Jinja2Templates):
        self._templates = templates
        self.router = APIRouter(prefix="/service")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route("/terms", self._terms, methods=["GET"])
        self.router.add_api_route("/privacy", self._privacy, methods=["GET"])

    async def _terms(self, request: Request):
        return self._templates.TemplateResponse("service/terms.html", {"request": request})

    async def _privacy(self, request: Request):
        return self._templates.TemplateResponse("service/privacy.html", {"request": request})
