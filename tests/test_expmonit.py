import pytest
from fotoniq.exp_monit import ExpMoniDB


@pytest.fixture(scope="session")
def database_client_instance():
    return ExpMoniDB()

def test_databse_client_instanciation(database_client_instance):
    db =database_client_instance
