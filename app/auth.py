"""Firebase token verification using google-auth, matching the course example.

The course PaaS-by-example.pdf (Example 03) verifies Firebase ID tokens with
``google.oauth2.id_token.verify_firebase_token``. We follow that exact pattern
instead of the firebase-admin SDK so the project stays inside the libraries
introduced in the course materials.
"""
import google.oauth2.id_token
from google.auth.transport import requests as google_requests


_firebase_request_adapter = google_requests.Request()


def verify_firebase_id_token(id_token: str) -> dict | None:
    """Validate a Firebase ID token taken from the ``token`` cookie.

    Returns the decoded claims dictionary when the token is valid, or ``None``
    when the cookie is missing/invalid. Mirrors how Example 03 logs validation
    errors to the console rather than raising to the route handler.
    """
    if not id_token:
        return None

    try:
        return google.oauth2.id_token.verify_firebase_token(
            id_token, _firebase_request_adapter
        )
    except ValueError as err:
        print(f"Firebase token verification failed: {err}")
        return None
