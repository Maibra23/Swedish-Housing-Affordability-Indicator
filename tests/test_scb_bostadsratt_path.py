"""Regression tests for live bostadsrätt SCB path resolution."""

import pandas as pd
import requests

from data import scb_client


def test_fetch_bostadsratt_price_uses_live_bo0501c_fallback(monkeypatch):
    """Fetch resolves to the known live BR price table path."""
    attempted_paths = []
    captured = {}

    def fake_get_table_metadata(path):
        attempted_paths.append(path)
        if path == "BO/BO0501/BO0501C/FastprisBRFRegionAr":
            return {
                "variables": [
                    {
                        "code": "Region",
                        "text": "region",
                        "values": ["00", "01", "03"],
                        "valueTexts": ["Riket", "Stockholms län", "Uppsala län"],
                    },
                    {
                        "code": "ContentsCode",
                        "text": "tabellinnehåll",
                        "values": ["A", "B", "C"],
                        "valueTexts": ["Antal", "Medelpris i tkr", "Medianpris i tkr"],
                    },
                    {
                        "code": "Tid",
                        "text": "år",
                        "values": ["2023", "2024"],
                        "valueTexts": ["2023", "2024"],
                    },
                ]
            }
        raise requests.HTTPError(f"404 for {path}")

    def fake_chunked_fetch(table_path, variables, selection_overrides=None, chunk_var=None, chunk_size=50):
        captured["table_path"] = table_path
        captured["selection_overrides"] = selection_overrides
        captured["chunk_var"] = chunk_var
        return pd.DataFrame({"Region_code": ["01"], "Region": ["Stockholms län"], "value": [3500]})

    monkeypatch.setattr(scb_client, "_get_table_metadata", fake_get_table_metadata)
    monkeypatch.setattr(scb_client, "_chunked_fetch", fake_chunked_fetch)
    monkeypatch.setattr(scb_client, "_save_and_return", lambda df, name: df)

    df = scb_client.fetch_bostadsratt_price(force=True)

    assert not df.empty
    assert "BO/BO0501/BO0501C/FastprisBRFRegionAr" in attempted_paths
    assert captured["table_path"] == "BO/BO0501/BO0501C/FastprisBRFRegionAr"
    assert captured["chunk_var"] == "Region"
    assert captured["selection_overrides"] == {"ContentsCode": ["B"]}
