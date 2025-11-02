import pytest
from unittest.mock import patch

# Ajustado para importar o módulo correto (api.utils.mongo)
from importlib import import_module
mongo_module = import_module("api.utils.mongo")


def test_mongo_get_config_handles_connection_error(monkeypatch):
    # simular falha ao obter cliente MongoDB (get_mongo_client)
    monkeypatch.setattr("api.views.get_mongo_client", lambda: (_ for _ in ()).throw(Exception("connection failed")))
    # chamar get_template_from_mongo e garantir que retorne None em caso de erro
    from importlib import import_module as im
    views = im("api.views")
    doc = views.get_template_from_mongo("x", "xml")
    assert doc is None