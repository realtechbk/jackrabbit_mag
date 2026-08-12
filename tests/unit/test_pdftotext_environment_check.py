"""check_pdftotext_is_poppler() is what turns 'the wrong pdftotext build is
on PATH' from a mysterious reconciliation-variance failure into a clear,
actionable one (see importers/jackrabbit/importer.py's extract(), and the
module docstring on revenue_summary_parser.py). These tests fake subprocess
output rather than depending on any specific pdftotext actually being
installed -- this repo's own dev environment currently only has an Xpdf
build (see tests/integration/test_jackrabbit_importer.py's module docstring),
so a test that required a real Poppler binary to pass could not run here.
"""

from __future__ import annotations

import subprocess

import pytest

from cfo_platform.core.exceptions import ConfigurationError
from cfo_platform.importers.jackrabbit.revenue_summary_parser import check_pdftotext_is_poppler


def _fake_run(stdout="", stderr="", returncode=0, raise_not_found=False):
    def run(args, **kwargs):
        if raise_not_found:
            raise FileNotFoundError(args[0])
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr=stderr)

    return run


def test_poppler_banner_passes(monkeypatch):
    monkeypatch.setattr(
        "cfo_platform.importers.jackrabbit.revenue_summary_parser.subprocess.run",
        _fake_run(stderr="pdftotext version 24.08.0\n"
                          "Copyright 2005-2024 The Poppler Developers - http://poppler.freedesktop.org\n"
                          "Copyright 1996-2011, 2022 Glyph & Cog, LLC"),
    )
    check_pdftotext_is_poppler()  # must not raise


def test_xpdf_banner_is_rejected(monkeypatch):
    """Xpdf's own banner (verified against the real binary in this repo's
    dev environment) never mentions Poppler, even though it shares the
    'Glyph & Cog' copyright line Poppler also carries -- that's exactly why
    the check can't key off that line."""
    monkeypatch.setattr(
        "cfo_platform.importers.jackrabbit.revenue_summary_parser.subprocess.run",
        _fake_run(stderr="pdftotext version 4.00\nCopyright 1996-2017 Glyph & Cog, LLC", returncode=99),
    )
    with pytest.raises(ConfigurationError, match="not a Poppler build"):
        check_pdftotext_is_poppler()


def test_missing_binary_raises_configuration_error_not_a_crash(monkeypatch):
    monkeypatch.setattr(
        "cfo_platform.importers.jackrabbit.revenue_summary_parser.subprocess.run",
        _fake_run(raise_not_found=True),
    )
    with pytest.raises(ConfigurationError, match="not found"):
        check_pdftotext_is_poppler()


def test_explicit_path_argument_is_used_verbatim(monkeypatch):
    captured = {}

    def run(args, **kwargs):
        captured["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="Poppler")

    monkeypatch.setattr(
        "cfo_platform.importers.jackrabbit.revenue_summary_parser.subprocess.run", run
    )
    check_pdftotext_is_poppler(r"C:\tools\poppler\pdftotext.exe")
    assert captured["args"][0] == r"C:\tools\poppler\pdftotext.exe"


def test_settings_pdftotext_path_is_used_when_no_explicit_path_given(monkeypatch):
    from cfo_platform.settings import get_settings

    monkeypatch.setenv("CFO_PDFTOTEXT_PATH", r"C:\tools\poppler\pdftotext.exe")
    get_settings.cache_clear()

    captured = {}

    def run(args, **kwargs):
        captured["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="Poppler")

    monkeypatch.setattr(
        "cfo_platform.importers.jackrabbit.revenue_summary_parser.subprocess.run", run
    )
    try:
        check_pdftotext_is_poppler()
        assert captured["args"][0] == r"C:\tools\poppler\pdftotext.exe"
    finally:
        get_settings.cache_clear()
