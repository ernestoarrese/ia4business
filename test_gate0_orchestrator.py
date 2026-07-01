from gate0_orchestrator import Gate0Orchestrator


def test_orchestrator_can_be_created():
    orchestrator = Gate0Orchestrator()
    assert orchestrator is not None


def test_orchestrator_has_run_method():
    orchestrator = Gate0Orchestrator()
    assert callable(orchestrator.run)
