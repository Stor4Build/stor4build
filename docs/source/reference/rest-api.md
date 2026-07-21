# Web API Reference

The current web API is Flask-based and accepts JSON inputs for the `/simulate` route. The API is expected to move to FastAPI; when that implementation becomes active, FastAPI's generated OpenAPI schema should become the source of truth for this page.

The intended documentation flow is:

1. Generate `openapi.json` from the FastAPI application.
2. Commit or publish that generated schema as a documentation artifact.
3. Render the schema in the Sphinx reference section for HTML and PDF output.
4. Optionally link to Swagger UI or ReDoc for an interactive web-only explorer.

Until the FastAPI migration lands, see the input schema reference for the checked-in schema describing accepted request data.