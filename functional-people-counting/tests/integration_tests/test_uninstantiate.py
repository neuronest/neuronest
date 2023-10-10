import pytest
from core.client.model_instantiator import ModelInstantiatorClient


@pytest.mark.dependency(depends=["test_count_people_async", "test_count_people_sync"])
def test_uninstantiate(
    model_instantiator_client: ModelInstantiatorClient,
    model_name: str,
):
    model_instantiator_client.uninstantiate(model_name)
