import pytest
from django.core.exceptions import ValidationError
from core.models import DeviceProfile, DeviceConfig


@pytest.mark.django_db
def test_deviceprofile_port_validation():
    """
    Valida que os validators de Min/Max em port_server/backup_port disparam ValidationError
    quando chamamos full_clean() com valores fora do intervalo.
    """
    p = DeviceProfile(name="TP", port_server=5060, backup_port=5060)
    # valor válido não deve levantar
    p.full_clean()  # should not raise

    # valor inválido (acima do máximo) deve levantar ValidationError ao chamar full_clean()
    p.port_server = 70000
    with pytest.raises(ValidationError):
        p.full_clean()

    # testar também backup_port inválido
    p.port_server = 5060
    p.backup_port = 70000
    with pytest.raises(ValidationError):
        p.full_clean()


@pytest.mark.django_db
def test_deviceprofile_str_and_metadata_default():
    p = DeviceProfile.objects.create(name="PSTR")
    assert str(p) == "PSTR"
    assert isinstance(p.metadata, dict)


@pytest.mark.django_db
def test_deviceconfig_str_returns_identifier_or_mac():
    p = DeviceProfile.objects.create(name="PX")
    d = DeviceConfig.objects.create(profile=p, identifier="id-1", mac_address="aa11")
    assert str(d) == "id-1"
    d.identifier = ""
    d.save()
    # depois de salvar sem identifier, __str__ deve retornar mac_address (normalizado)
    assert "aa11" in str(d)