import json
from types import SimpleNamespace
from django.test import RequestFactory

from importlib import import_module
oauth_views = import_module("api.oauth_views")


def _unwrap(func):
    """
    Desembrulha todos os decorators aplicados a `func` até alcançar a função original.
    Alguns decorators (como oauth protected_resource e require_GET) ainda estavam ativos
    mesmo chamando __wrapped__ apenas uma vez; por isso iteramos até não existir mais __wrapped__.
    """
    f = func
    while hasattr(f, "__wrapped__"):
        f = f.__wrapped__
    return f


def test_whoami_returns_user_info():
    factory = RequestFactory()
    request = factory.get("/oauth/whoami")
    # montar um objeto user simples (não precisamos do DB)
    request.user = SimpleNamespace(username="bob", email="bob@example.com", is_authenticated=True)
    # token pode estar em request.oauth2_provider_token ou request.auth
    request.oauth2_provider_token = "fake-token"

    # chamar a função original sem decorators para testar apenas a lógica interna
    orig = _unwrap(oauth_views.whoami)
    resp = orig(request)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode("utf-8"))
    assert data["username"] == "bob"
    assert data["email"] == "bob@example.com"
    assert data["is_authenticated"] is True
    assert data["token_present"] is True
    assert "timestamp" in data


def test_whoami_handles_missing_user_and_token():
    factory = RequestFactory()
    request = factory.get("/oauth/whoami")
    # sem user/token
    request.user = None
    request.oauth2_provider_token = None

    orig = _unwrap(oauth_views.whoami)
    resp = orig(request)
    assert resp.status_code == 200
    data = json.loads(resp.content.decode("utf-8"))
    assert data["username"] is None
    assert data["is_authenticated"] is False
    assert data["token_present"] is False