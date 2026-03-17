import django_machine_auth as dma


def test_top_level_exports_are_stable():
    assert dma.__version__
    assert dma.api_key_module
    assert dma.MachineAPIKeyAuthentication
    assert dma.MachineAuthPermission
    assert dma.MachineAPIKeyRateThrottle
    assert dma.MachineAuthViewSet


def test_import_paths_for_primary_entrypoints():
    from django_machine_auth.authentication import MachineAPIKeyAuthentication
    from django_machine_auth.decorators import api_key_module
    from django_machine_auth.permissions import MachineAuthPermission
    from django_machine_auth.throttling import MachineAPIKeyRateThrottle
    from django_machine_auth.views import MachineAuthViewSet

    assert MachineAPIKeyAuthentication
    assert api_key_module
    assert MachineAuthPermission
    assert MachineAPIKeyRateThrottle
    assert MachineAuthViewSet
