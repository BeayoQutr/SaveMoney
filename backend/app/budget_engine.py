from datetime import date

from app.schemas import GeneratePlanRequest, GeneratePlanResponse
from app.schemas import AdjustPlanRequest, AdjustPlanResponse


def generate_saving_plan(data: GeneratePlanRequest) -> GeneratePlanResponse:
    today = date.today()
    remaining_days = (data.deadline - today).days

    if remaining_days <= 0:
        return GeneratePlanResponse(
            remaining_days=0,
            daily_saving=0,
            monthly_available=0,
            daily_available=0,
            target_amount=data.target_amount,
            feasibility_score=0,
            minimum_living_cost=data.minimum_living_cost,
            safe_saving_capacity=0,
            status="invalid",
            message="截止日期必须晚于今天"
        )

    monthly_available = data.monthly_income - data.fixed_expenses

    if monthly_available <= 0:
        return GeneratePlanResponse(
            remaining_days=remaining_days,
            daily_saving=0,
            monthly_available=round(monthly_available, 2),
            daily_available=0,
            target_amount=data.target_amount,
            feasibility_score=0,
            minimum_living_cost=data.minimum_living_cost,
            safe_saving_capacity=round(monthly_available - data.minimum_living_cost, 2),
            status="impossible",
            message="固定支出已经大于或等于收入，当前无法制定攒钱计划"
        )

    safe_saving_capacity = monthly_available - data.minimum_living_cost

    if safe_saving_capacity <= 0:
        return GeneratePlanResponse(
            remaining_days=remaining_days,
            daily_saving=0,
            monthly_available=round(monthly_available, 2),
            daily_available=0,
            target_amount=data.target_amount,
            feasibility_score=0,
            minimum_living_cost=data.minimum_living_cost,
            safe_saving_capacity=round(safe_saving_capacity, 2),
            status="impossible",
            message="扣除固定支出和最低生活费后，当前没有可用于攒钱的余额"
        )

    daily_saving = round(data.target_amount / remaining_days, 2)
    daily_available = round(safe_saving_capacity / 30, 2)

    if daily_available <= 0:
        feasibility_score = 0
    elif daily_saving <= daily_available:
        feasibility_score = 100
    else:
        feasibility_score = int((daily_available / daily_saving) * 100)
        if feasibility_score < 0:
            feasibility_score = 0
        elif feasibility_score > 100:
            feasibility_score = 100

    if daily_saving > daily_available:
        status = "hard"
        message = "目标较紧张，每日需要存的钱超过当前日均可支配金额"
    else:
        status = "ok"
        message = "目标可行，可以按当前计划执行"

    return GeneratePlanResponse(
        remaining_days=remaining_days,
        daily_saving=daily_saving,
        monthly_available=round(monthly_available, 2),
        daily_available=daily_available,
        target_amount=data.target_amount,
        feasibility_score=feasibility_score,
        minimum_living_cost=data.minimum_living_cost,
        safe_saving_capacity=round(safe_saving_capacity, 2),
        status=status,
        message=message
    )


def adjust_saving_plan(data: AdjustPlanRequest) -> AdjustPlanResponse:
    remaining_amount = round(data.target_amount - data.saved_amount, 2)

    if remaining_amount <= 0:
        new_daily_saving = 0.0
        adjustment_per_day = round(-data.planned_daily_saving, 2)
        return AdjustPlanResponse(
            remaining_amount=remaining_amount,
            today_gap=0.0,
            new_daily_saving=new_daily_saving,
            adjustment_per_day=adjustment_per_day,
            status="ok",
            message="目标已达成，无需继续攒钱",
        )

    actual_saving_today = max(data.daily_available - data.actual_expense_today, 0)
    actual_saving_today = round(actual_saving_today, 2)
    today_gap = round(data.planned_daily_saving - actual_saving_today, 2)
    adjusted_remaining_amount = round(remaining_amount + today_gap, 2)
    new_daily_saving = round(adjusted_remaining_amount / data.remaining_days, 2)
    adjustment_per_day = round(new_daily_saving - data.planned_daily_saving, 2)

    if new_daily_saving <= data.daily_available:
        status = "ok"
        message = "计划已调整，后续每日存钱压力仍在可承受范围内"
    else:
        status = "hard"
        message = "计划已调整，但后续每日存钱压力较大，建议降低目标或延长期限"

    return AdjustPlanResponse(
        remaining_amount=remaining_amount,
        today_gap=today_gap,
        new_daily_saving=new_daily_saving,
        adjustment_per_day=adjustment_per_day,
        status=status,
        message=message,
    )
