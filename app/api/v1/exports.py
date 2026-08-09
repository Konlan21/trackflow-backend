"""
Export endpoints (Phase 8):
  GET /user/export/csv  -> combined income + expense transactions as CSV
  GET /user/export/pdf  -> full styled report (summary + transaction table) as PDF
"""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.expenditure import Expenditure
from app.models.income import Income
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])


async def _get_combined_transactions(db: AsyncSession, user_id):
    incomes = (
        await db.execute(select(Income).where(Income.user_id == user_id).order_by(Income.created_at.desc()))
    ).scalars().all()
    expenses = (
        await db.execute(select(Expenditure).where(Expenditure.user_id == user_id).order_by(Expenditure.created_at.desc()))
    ).scalars().all()

    rows = []
    for i in incomes:
        rows.append({
            "date": i.created_at,
            "type": "Income",
            "name": i.nameOfRevenue,
            "category": "-",
            "amount": i.amount,
        })
    for e in expenses:
        rows.append({
            "date": e.created_at,
            "type": "Expense",
            "name": e.nameOfItem,
            "category": e.category.value,
            "amount": e.amount,
        })
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


@router.get("/csv")
async def export_csv(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = await _get_combined_transactions(db, current_user.id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Type", "Name", "Category", "Amount"])
    for r in rows:
        writer.writerow([
            r["date"].strftime("%Y-%m-%d %H:%M"),
            r["type"],
            r["name"],
            r["category"],
            f"{r['amount']:.2f}",
        ])
    buffer.seek(0)

    filename = f"trackflow_transactions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/pdf")
async def export_pdf(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = await _get_combined_transactions(db, current_user.id)

    total_income = sum((r["amount"] for r in rows if r["type"] == "Income"), start=0)
    total_expense = sum((r["amount"] for r in rows if r["type"] == "Expense"), start=0)
    net_balance = total_income - total_expense

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20, spaceAfter=4)
    subtitle_style = ParagraphStyle("SubtitleStyle", parent=styles["Normal"], textColor=colors.grey, spaceAfter=20)
    section_style = ParagraphStyle("SectionStyle", parent=styles["Heading2"], spaceBefore=16, spaceAfter=10)

    elements = []
    elements.append(Paragraph("TrackFlow — Financial Report", title_style))
    elements.append(Paragraph(
        f"Generated for {current_user.first_name} {current_user.last_name} on "
        f"{datetime.utcnow().strftime('%B %d, %Y')}",
        subtitle_style,
    ))

    # --- Summary section ---
    elements.append(Paragraph("Summary", section_style))
    summary_data = [
        ["Total Income", f"${total_income:.2f}"],
        ["Total Expenses", f"${total_expense:.2f}"],
        ["Net Balance", f"${net_balance:.2f}"],
        ["Total Transactions", str(len(rows))],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 6 * cm])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1, 2), (1, 2), colors.HexColor("#0f9d58") if net_balance >= 0 else colors.HexColor("#d93025")),
        ("FONTNAME", (1, 2), (1, 2), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e0e0e0")),
    ]))
    elements.append(summary_table)

    # --- Transactions table ---
    elements.append(Paragraph("Transactions", section_style))
    table_data = [["Date", "Type", "Name", "Category", "Amount"]]
    for r in rows:
        table_data.append([
            r["date"].strftime("%Y-%m-%d"),
            r["type"],
            r["name"],
            r["category"],
            f"${r['amount']:.2f}",
        ])

    transactions_table = Table(table_data, colWidths=[2.5 * cm, 2.2 * cm, 5 * cm, 3 * cm, 3 * cm], repeatRows=1)
    transactions_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (4, 0), (4, -1), "RIGHT"),
    ]))
    elements.append(transactions_table)

    doc.build(elements)
    buffer.seek(0)

    filename = f"trackflow_report_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )