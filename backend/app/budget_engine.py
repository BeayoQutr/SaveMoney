from datetime import date

from app.schemas import GeneratePlanRequest, GeneratePlanResponse


def generate_saving_plan(data: GeneratePlanRequest) -> GeneratePlanResponse:
    today = date.today()
    remaining_days = (data.deadline - today).days

    if remaining_days <= 0:
        return GeneratePlanResponse(
            remaining_days=0,
            daily_saving=0,
            monthly_available=0,
            status="invalid",
            message="截止日期必须晚于今天"
        )

    monthly_available = data.monthly_income - data.fixed_expenses

    if monthly_available <= 0:
        return GeneratePlanResponse(
            remaining_days=remaining_days,
            daily_saving=0,
            monthly_available=monthly_available,
            status="impossible",
            message="固定支出已经大于或等于收入，当前无法制定攒钱计划"
        )

    daily_saving = round(data.target_amount / remaining_days, 2)
    daily_available = monthly_available / 30

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
        status=status,
        message=message
    )