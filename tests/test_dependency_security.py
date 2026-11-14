"""Regression tests for the locked Soup Sieve security floor."""

from __future__ import annotations

import importlib.metadata

from bs4 import BeautifulSoup
from packaging.version import Version


def test_soupsieve_lock_is_on_fixed_release():
    assert Version(importlib.metadata.version("soupsieve")) >= Version("4.1")


def test_beautifulsoup_css_selection_works_with_fixed_soupsieve():
    soup = BeautifulSoup(
        '<main><section class="target"><span data-role="value">ok</span></section></main>',
        "html.parser",
    )
    assert soup.select_one("main > section.target span[data-role=value]").text == "ok"
