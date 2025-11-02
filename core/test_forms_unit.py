import pytest
from importlib import import_module

@pytest.mark.django_db
def test_deviceprofile_form_valid_minimal():
    """
    DeviceProfileForm deve ser válido com os campos mínimos exigidos pelo ModelForm.
    Note que alguns campos do modelo (port_server, protocol_type, backup_port, register_ttl)
    são exigidos pelo ModelForm apesar de terem default no model, então precisamos submetê-los.
    """
    forms = import_module("core.forms")
    assert hasattr(forms, "DeviceProfileForm"), "DeviceProfileForm não encontrado em core.forms"
    DeviceProfileForm = forms.DeviceProfileForm

    data = {
        "name": "Profile Test",
        "port_server": 5060,
        "protocol_type": "UDP",
        "backup_port": 5060,
        "register_ttl": 3600,
    }
    form = DeviceProfileForm(data=data)
    assert form.is_valid(), f"Form rejeitou dados válidos: {form.errors}"


@pytest.mark.django_db
def test_deviceprofile_form_invalid_missing_name():
    """
    DeviceProfileForm sem 'name' deve ser inválido.
    """
    forms = import_module("core.forms")
    DeviceProfileForm = forms.DeviceProfileForm

    data = {
        "name": "",
        "port_server": 5060,
        "protocol_type": "UDP",
        "backup_port": 5060,
        "register_ttl": 3600,
    }
    form = DeviceProfileForm(data=data)
    assert not form.is_valid()
    assert "name" in form.errors


@pytest.mark.django_db
def test_deviceconfig_form_clean_mac_and_valid():
    """
    DeviceConfigForm deve aceitar MAC com separadores (clean_mac_address apenas strip)
    e ser válido com campos mínimos.
    """
    forms = import_module("core.forms")
    DeviceConfigForm = forms.DeviceConfigForm

    data = {
        "identifier": "device-1",
        "mac_address": "AA:BB:CC:11:22:33",
    }
    form = DeviceConfigForm(data=data)
    assert form.is_valid(), f"DeviceConfigForm rejeitou dados válidos: {form.errors}"

    # testar método de limpeza customizado (retorna string stripped)
    cleaned_mac = form.clean_mac_address()
    assert isinstance(cleaned_mac, str)
    assert cleaned_mac.strip() == "AA:BB:CC:11:22:33".strip()