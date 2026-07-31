from fpdf import FPDF
from datetime import datetime
import os


def generate_rekapan_pdf(transactions: list, user: str, bulan: int, tahun: int, saldo_akhir: int) -> str:
    total_masuk = sum(t["amount"] for t in transactions if t["type"] == "pemasukan")
    total_keluar = sum(t["amount"] for t in transactions if t["type"] == "pengeluaran")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Rekapan Keuangan DOIKITA", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"User: {user}", ln=True)
    pdf.cell(0, 7, f"Periode: {bulan}/{tahun}", ln=True)
    pdf.cell(0, 7, f"Total Pemasukan: Rp {total_masuk:,}", ln=True)
    pdf.cell(0, 7, f"Total Pengeluaran: Rp {total_keluar:,}", ln=True)
    pdf.cell(0, 7, f"Saldo Akhir: Rp {saldo_akhir:,}", ln=True)
    pdf.ln(5)

    col_widths = [8, 25, 30, 25, 30, 60]
    headers = ["#", "Tanggal", "Tipe", "Kategori", "Jumlah", "Deskripsi"]

    pdf.set_font("Helvetica", "B", 9)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for i, t in enumerate(transactions, 1):
        tipe = "Pemasukan" if t["type"] == "pemasukan" else "Pengeluaran"
        tgl = t.get("created_at", "")[:10]
        nominal = f"Rp {t['amount']:,}"
        row = [str(i), tgl, tipe, t["category"], nominal, t["description"]]
        for j, val in enumerate(row):
            pdf.cell(col_widths[j], 6, val, border=1)
        pdf.ln()

    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, f"Dibuat pada {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")

    pdf_dir = os.path.join(os.path.dirname(__file__), "..", "pdf")
    os.makedirs(pdf_dir, exist_ok=True)
    filename = f"rekapan_{user}_{tahun}_{bulan:02d}.pdf"
    filepath = os.path.join(pdf_dir, filename)

    pdf.output(filepath)
    return filepath
