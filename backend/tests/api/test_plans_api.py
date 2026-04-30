from datetime import date, timedelta


def test_saving_plan_money_fields_are_stored_as_cents(api_client) -> None:
    from app.database import SessionLocal
    from app.models import SavingPlan

    response = api_client.post(
        "/plans/generate",
        json={
            "monthly_income": 5000.12,
            "fixed_expenses": 1000.34,
            "target_amount": 1234.56,
            "deadline": (date.today() + timedelta(days=60)).isoformat(),
            "identity": "worker",
            "minimum_living_cost": 999.99,
        },
    )
    assert response.status_code == 200

    db = SessionLocal()
    try:
        plan = db.query(SavingPlan).one()
        assert plan.target_amount_cents == 123456
        assert plan.monthly_income_cents == 500012
        assert plan.fixed_expenses_cents == 100034
        assert plan.minimum_living_cost_cents == 99999
        assert plan.saved_amount_cents == 0

        update_response = api_client.put(
            f"/plans/{plan.id}",
            json={"saved_amount": 12.345},
        )
        assert update_response.status_code == 200
        db.refresh(plan)
        assert plan.saved_amount_cents == 1235
        assert update_response.json()["saved_amount"] == 12.35
    finally:
        db.close()


def test_current_saving_plan_returns_calculated_progress(api_client) -> None:
    deadline = date.today() + timedelta(days=10)
    create_response = api_client.post(
        "/plans/generate",
        json={
            "monthly_income": 5000,
            "fixed_expenses": 1000,
            "target_amount": 1000,
            "deadline": deadline.isoformat(),
            "identity": "worker",
            "minimum_living_cost": 1000,
        },
    )
    assert create_response.status_code == 200

    current = api_client.get("/plans/current")

    assert current.status_code == 200
    data = current.json()
    assert data["remaining_days"] == 10
    assert data["daily_saving"] == 100
    assert data["daily_available"] == 100
    assert data["plan"]["target_amount"] == 1000
