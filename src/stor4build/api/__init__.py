# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

from typing import Mapping, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from ..__about__ import __version__
from ..schema import SimulationRequest
from .service import APIError, MissingConfig, run_simulation_request
from .settings import load_settings


ERROR_RESPONSE = {
    "type": "object",
    "properties": {
        "error": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["error", "message"],
}


def create_app(config: Optional[Mapping[str, object]] = None) -> FastAPI:
    app = FastAPI(
        title="stor4build",
        version=__version__,
        description="The stor4build API for TES calculations",
    )

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.error, "message": exc.message})

    @app.exception_handler(MissingConfig)
    async def missing_config_handler(request: Request, exc: MissingConfig) -> JSONResponse:
        return JSONResponse(status_code=500, content={"error": "MissingConfig", "message": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": "Bad request", "message": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": "Bad request", "message": str(exc)})

    @app.post(
        "/simulate",
        responses={
            200: {
                "description": "TES simulation results as CSV.",
                "content": {
                    "text/csv": {
                        "schema": {"type": "string"},
                    }
                },
            },
            400: {"description": "Simulation input or domain validation error.", "content": {"application/json": {"schema": ERROR_RESPONSE}}},
            422: {"description": "Request validation error.", "content": {"application/json": {"schema": ERROR_RESPONSE}}},
            500: {"description": "Server or configuration error.", "content": {"application/json": {"schema": ERROR_RESPONSE}}},
        },
        summary="Simulate a TES technology, including sizing.",
    )
    async def simulate_route(payload: SimulationRequest) -> Response:
        settings = load_settings(config)
        response_txt = run_simulation_request(payload, settings)
        return Response(
            content=response_txt,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=results.csv"},
        )

    return app
