from database import SessionLocal
from report_generator import generate_pdf_report

def test_generate_pdf_report():
    db = SessionLocal()
    try:
        pdf_bytes = generate_pdf_report(db, lang="en")
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 500
        assert pdf_bytes.startswith(b"%PDF")
    finally:
        db.close()
