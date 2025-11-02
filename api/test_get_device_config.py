import pytest
from types import SimpleNamespace

# Testes para api.views.get_device_config — mocka _get_models para retornar um FakeDeviceConfig
from importlib import import_module
views = import_module("api.views")


class DoesNotExist(Exception):
    pass


class FakeObjects:
    def __init__(self, items):
        self.items = items

    def get(self, **kwargs):
        # aceita mac_address=norm and identifier=...
        if "mac_address" in kwargs:
            mac = kwargs["mac_address"]
            for it in self.items:
                if it.get("mac_address") == mac:
                    return SimpleNamespace(**it)
            raise DoesNotExist
        if "identifier" in kwargs:
            identifier = kwargs["identifier"]
            for it in self.items:
                if it.get("identifier") == identifier:
                    return SimpleNamespace(**it)
            raise DoesNotExist
        raise DoesNotExist


class FakeDeviceConfig:
    # adicionar atributo DoesNotExist para simular API do ORM
    DoesNotExist = DoesNotExist
    objects = FakeObjects(
        [
            {"identifier": "dev-1", "mac_address": "aabbcc112233"},
            {"identifier": "dev-2", "mac_address": "deadbeef"},
        ]
    )


@pytest.mark.parametrize(
    "identifier,expected_identifier",
    [
        ("dev-1", "dev-1"),
        ("aabb:cc:11:22:33", "dev-1"),  # mac with separators normalizes and matches first item
    ],
)
def test_get_device_config_by_identifier(monkeypatch, identifier, expected_identifier):
    # substituir o retorno de _get_models para usar FakeDeviceConfig
    monkeypatch.setattr(views, "_get_models", lambda: (FakeDeviceConfig, None, None))
    result = views.get_device_config(identifier)
    assert result is not None
    assert getattr(result, "identifier") == expected_identifier


def test_get_device_config_handles_missing(monkeypatch):
    monkeypatch.setattr(views, "_get_models", lambda: (FakeDeviceConfig, None, None))
    # identifier inexistente deve retornar None (e não lançar)
    result = views.get_device_config("non-existent")
    assert result is None