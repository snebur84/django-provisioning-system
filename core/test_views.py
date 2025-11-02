import re
import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from importlib import import_module

@pytest.mark.django_db
def test_profile_create_or_update_post_creates_profile():
    """
    Submete POST para a rota de criação de profile:
    - faz um GET inicial para obter o HTML do formulário (incluindo management form do inline formset);
    - extrai o nome exato do campo TOTAL_FORMS gerado pela view e monta os demais nomes do management form
      (INITIAL_FORMS, MIN_NUM_FORMS, MAX_NUM_FORMS) com valores adequados;
    - submete o POST com os campos obrigatórios do DeviceProfileForm e com os campos do management form,
      garantindo que o formset seja considerado válido mesmo sem registros de devices;
    - aceita redirect (301/302) como indicação de sucesso e valida que o objeto foi criado;
    - se a resposta for 200 (form re-renderizado) e o objeto não existir, extrai trechos do HTML para diagnóstico.
    """
    client = Client()
    User = get_user_model()
    # usuário precisa ser staff para acessar a view protegida por staff_required
    user = User.objects.create_user(username="testuser", password="testpass", is_staff=True)
    client.force_login(user)

    url = "/profiles/create/"

    # GET inicial para obter o form + management form do inlineformset
    get_resp = client.get(url)
    assert get_resp.status_code == 200
    html = get_resp.content.decode("utf-8", errors="replace")

    # tentar extrair o nome exato do campo TOTAL_FORMS gerado (p.ex. deviceconfig_set-TOTAL_FORMS)
    m = re.search(r'name=["\']([A-Za-z0-9_-]+-TOTAL_FORMS)["\']', html)
    if m:
        total_name = m.group(1)
        prefix = total_name.rsplit("-TOTAL_FORMS", 1)[0]
        initial_name = f"{prefix}-INITIAL_FORMS"
        min_name = f"{prefix}-MIN_NUM_FORMS"
        max_name = f"{prefix}-MAX_NUM_FORMS"
    else:
        # fallback conservador caso a extração falhe
        prefix = "deviceconfig_set"
        total_name = f"{prefix}-TOTAL_FORMS"
        initial_name = f"{prefix}-INITIAL_FORMS"
        min_name = f"{prefix}-MIN_NUM_FORMS"
        max_name = f"{prefix}-MAX_NUM_FORMS"

    # montar payload do POST com campos obrigatórios do DeviceProfileForm
    data = {
        "name": "NewProfileFromTest",
        "port_server": 5060,
        "protocol_type": "UDP",
        "backup_port": 5060,
        "register_ttl": 3600,
        # management form values: indicar que não há forms de devices submetidos
        total_name: "0",
        initial_name: "0",
        min_name: "0",
        max_name: "1000",
    }

    resp = client.post(url, data)
    assert resp.status_code in (200, 301, 302)

    models = import_module("core.models")
    exists = models.DeviceProfile.objects.filter(name="NewProfileFromTest").exists()

    if resp.status_code in (301, 302):
        assert exists, "Esperado que DeviceProfile tenha sido criado após redirect"
    else:
        # resp.status_code == 200 -> form re-renderizado. Se objeto não existe, falhar com diagnóstico.
        if not exists:
            # tentar extrair erros do contexto; se não, procurar no HTML por mensagens padrão do Django
            form_errors = None
            try:
                if hasattr(resp, "context") and resp.context:
                    for v in resp.context.values():
                        if hasattr(v, "errors") and v.errors:
                            form_errors = v.errors
                            break
            except Exception:
                form_errors = None

            if not form_errors:
                try:
                    text = resp.content.decode("utf-8", errors="replace")
                    snippets = []
                    if "This field is required." in text:
                        idx = text.find("This field is required.")
                        start = max(0, idx - 120)
                        end = min(len(text), idx + 120)
                        snippets.append(text[start:end])
                    if '<ul class="errorlist"' in text:
                        start = text.find('<ul class="errorlist"')
                        snippets.append(text[start:start+300])
                    if snippets:
                        form_errors = " | ".join(snippets)
                    else:
                        form_errors = text[:800]
                except Exception:
                    form_errors = "<não foi possível extrair trechos do HTML>"

            pytest.fail(f"POST retornou 200 e o DeviceProfile não foi criado. form_errors={form_errors}")