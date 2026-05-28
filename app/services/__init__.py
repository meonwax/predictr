"""Service-layer modules.

The convention in this project is:

* ``app/routes/*`` - thin HTTP handlers; parse input, call a service, render.
* ``app/services/*`` - business logic; talks to the DB and external resources,
  raises domain exceptions that the route layer maps to HTTP responses.
* ``app/security.py`` - pure crypto primitives, no DB / no FastAPI.
"""
