"""Suite-wide markers for the two slow kinds of test.

``browser``: starts the app or opens Chromium. Applied here to every test that
uses one of the browser fixtures, so a new browser test is marked without anyone
remembering to. About two thirds of the suite's run time.

``network``: talks to a live API. Marked where defined.

A quick rerun that skips both takes about a minute::

    pytest -m "not browser and not network"

Run the full suite before deploying.
"""

from __future__ import annotations

import pytest

_BROWSER_FIXTURES = {"browser", "server", "base_url"}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if _BROWSER_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.browser)
