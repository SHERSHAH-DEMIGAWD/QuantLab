"""Local REST boundary. Importing this module does not create a database."""

from .app import create_app

__all__ = ["create_app"]
