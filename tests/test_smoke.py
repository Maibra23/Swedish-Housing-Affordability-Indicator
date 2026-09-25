"""Smoke tests: editable install exposes src packages."""

import importlib


def test_import_data_package():
    importlib.import_module("data")


def test_import_indices_package():
    importlib.import_module("indices")


def test_import_forecast_package():
    """The package now holds the conditional projection and nothing fitted."""
    module = importlib.import_module("forecast.projection")
    assert hasattr(module, "project_all")


def test_import_kontantinsats_package():
    importlib.import_module("kontantinsats")


def test_import_scenario_package():
    importlib.import_module("scenario")


def test_import_ui_package():
    importlib.import_module("ui")
