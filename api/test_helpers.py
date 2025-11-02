import logging
import pytest
from django.test import RequestFactory
from importlib import import_module

helpers = import_module("api.views")


def test_parse_user_agent_valid():
    factory = RequestFactory()
    ua = "Ale H2P 2.10 3c28a60357a0"
    request = factory.get("/", HTTP_USER_AGENT=ua)
    out = helpers.parse_user_agent(request)
    assert out == ("Ale", "H2P", "2.10", "3c28a60357a0")


def test_parse_user_agent_too_short(caplog):
    factory = RequestFactory()
    request = factory.get("/", HTTP_USER_AGENT="short")
    # capturar mensagens DEBUG do logger do módulo
    caplog.set_level(logging.DEBUG, logger="api.views")
    out = helpers.parse_user_agent(request)
    assert out is None
    # garantir que a mensagem de debug foi registrada
    assert any("User-Agent parsing failed" in r.message for r in caplog.records)


def test_extract_public_ip_prefers_non_private():
    factory = RequestFactory()
    # X-Forwarded-For com primeiro privado e depois público
    xff = "10.0.0.1, 1.2.3.4"
    request = factory.get("/", **{"HTTP_X_FORWARDED_FOR": xff})
    out = helpers._extract_public_ip(request)
    assert out == "1.2.3.4"

def test_extract_public_ip_fallback_remote_addr():
    factory = RequestFactory()
    request = factory.get("/", REMOTE_ADDR="1.2.3.4")
    out = helpers._extract_public_ip(request)
    assert out == "1.2.3.4"