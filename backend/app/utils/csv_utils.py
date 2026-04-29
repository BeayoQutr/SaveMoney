import csv
import io
from datetime import date

from fastapi.responses import Response

from app.models import Expense
from app.utils.money import round_money


def build_expenses_csv_response(
    rows: list[Expense],
    start_date: date,
    end_date: date,
) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "amount", "note", "date", "category"])
    for expense in rows:
        writer.writerow(
            [
                expense.id,
                f"{round_money(expense.amount):.2f}",
                expense.note,
                expense.date.isoformat(),
                expense.category,
            ]
        )

    filename = f"expenses_{start_date.isoformat()}_to_{end_date.isoformat()}.csv"

    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
