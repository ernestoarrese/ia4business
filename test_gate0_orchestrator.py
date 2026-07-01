from gate0_orchestrator import Gate0Orchestrator


def test_orchestrator_can_be_created():
    orchestrator = Gate0Orchestrator()
    assert orchestrator is not None
