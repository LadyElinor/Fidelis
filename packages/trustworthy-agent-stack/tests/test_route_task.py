from scripts.route_task import classify_task


def test_picobot_route_for_simple_reminder():
    decision = classify_task("Remind me in 20 minutes to check the laundry")
    assert decision.route == "picobot"


def test_openclaw_route_for_repo_synthesis():
    decision = classify_task("Compare these repos and propose an integration architecture")
    assert decision.route == "openclaw"


def test_never_auto_route_for_production_deploy():
    decision = classify_task("Deploy this change to production")
    assert decision.route == "never_auto_route"


def test_uncertain_defaults_upward():
    decision = classify_task("Help me think through this confusing project situation")
    assert decision.route == "openclaw"
