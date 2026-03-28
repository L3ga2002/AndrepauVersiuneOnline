"""Generate test invoice PDFs for ANDREPAU POS NIR import testing"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os

OUTPUT_DIR = "/app/backend/static/test_invoices"
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=14, alignment=TA_CENTER)
normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9)
small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8)
bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')

def create_invoice(filename, invoice_data):
    doc = SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, filename),
        pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm
    )
    elements = []

    # Title
    elements.append(Paragraph(f"Factura", title_style))
    elements.append(Paragraph(f"<b>{invoice_data['invoice_number']}</b>", ParagraphStyle('', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 5*mm))

    # Header info
    header_data = [
        [Paragraph(f"<b>Data emiterii:</b> {invoice_data['date']}", small_style),
         Paragraph(f"<b>Termen plata:</b> {invoice_data['due_date']}", small_style)],
    ]
    header_table = Table(header_data, colWidths=[90*mm, 90*mm])
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))

    # Supplier / Customer
    supplier_customer = [
        [Paragraph("<b>Furnizor:</b>", bold_style), Paragraph("<b>Cumparator:</b>", bold_style)],
        [Paragraph(invoice_data['supplier_name'], normal_style), Paragraph("ANDREPAU S.R.L.", normal_style)],
        [Paragraph(f"CUI: {invoice_data['supplier_cui']}", small_style), Paragraph("CUI: 21385520", small_style)],
        [Paragraph(f"Reg. Com.: {invoice_data['supplier_reg']}", small_style), Paragraph("Reg. Com.: J01/234/2020", small_style)],
        [Paragraph(f"Adresa: {invoice_data['supplier_address']}", small_style), Paragraph("Adresa: Str. Principala 10, Alba Iulia", small_style)],
    ]
    sc_table = Table(supplier_customer, colWidths=[90*mm, 90*mm])
    sc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(sc_table)
    elements.append(Spacer(1, 8*mm))

    # Products table
    table_data = [
        [Paragraph("<b>Nr.</b>", small_style),
         Paragraph("<b>Denumire produs/serviciu</b>", small_style),
         Paragraph("<b>U.M.</b>", small_style),
         Paragraph("<b>Cant.</b>", small_style),
         Paragraph("<b>Pret unitar\n(RON fara TVA)</b>", small_style),
         Paragraph("<b>Valoare\n(RON)</b>", small_style),
         Paragraph("<b>TVA\n(RON)</b>", small_style)]
    ]

    total_value = 0
    total_tva = 0
    for idx, item in enumerate(invoice_data['items'], 1):
        value = item['qty'] * item['price']
        tva = round(value * 0.19, 2)
        total_value += value
        total_tva += tva
        table_data.append([
            str(idx),
            Paragraph(item['name'], small_style),
            item['um'],
            str(item['qty']),
            f"{item['price']:.2f}",
            f"{value:.2f}",
            f"{tva:.2f}"
        ])

    # Totals
    table_data.append(['', Paragraph('<b>Total fara TVA</b>', small_style), '', '', '', f'{total_value:.2f}', ''])
    table_data.append(['', Paragraph('<b>TVA 19%</b>', small_style), '', '', '', '', f'{total_tva:.2f}'])
    table_data.append(['', Paragraph('<b>TOTAL DE PLATA</b>', bold_style), '', '', '', '', f'{total_value + total_tva:.2f}'])

    product_table = Table(table_data, colWidths=[10*mm, 70*mm, 15*mm, 15*mm, 25*mm, 22*mm, 22*mm])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
        ('LINEBELOW', (0, -3), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 10*mm))

    # Footer
    elements.append(Paragraph(f"Pagina 1 din 1", ParagraphStyle('', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER)))

    doc.build(elements)
    print(f"Created: {filename}")


# Invoice 1: DEDEMAN - materiale constructii diverse
create_invoice("factura_DEDEMAN_FV2024001.pdf", {
    "invoice_number": "FV 2024001",
    "date": "25.03.2026",
    "due_date": "24.04.2026",
    "supplier_name": "DEDEMAN S.R.L.",
    "supplier_cui": "14520250",
    "supplier_reg": "J08/1111/2002",
    "supplier_address": "Str. Barcarilor 16, Bacau",
    "items": [
        {"name": "CIMENT ROMCIM 40KG", "um": "sac", "qty": 50, "price": 22.50},
        {"name": "FIER BETON PC52 D12 L=12M", "um": "buc", "qty": 100, "price": 38.00},
        {"name": "CARAMIDA PLINA PRESATA 250x120x65", "um": "buc", "qty": 500, "price": 1.20},
        {"name": "MORTAR M10 WEBER 40KG", "um": "sac", "qty": 30, "price": 18.50},
        {"name": "PLASA SUDATA 2X5M OC50 D4", "um": "buc", "qty": 20, "price": 45.00},
        {"name": "ADEZIV GRESIE CERESIT CM11 25KG", "um": "sac", "qty": 40, "price": 28.90},
        {"name": "POLISTIREN EXPANDAT 10CM EPS80", "um": "mp", "qty": 100, "price": 12.50},
        {"name": "RIGIPS RB 12.5MM 2600X1200", "um": "buc", "qty": 50, "price": 32.00},
    ]
})

# Invoice 2: HORNBACH - vopsele si lacuri  
create_invoice("factura_HORNBACH_HB50234.pdf", {
    "invoice_number": "HB 50234",
    "date": "26.03.2026",
    "due_date": "25.04.2026",
    "supplier_name": "HORNBACH ROMANIA S.R.L.",
    "supplier_cui": "18320450",
    "supplier_reg": "J40/5555/2006",
    "supplier_address": "Sos. Berceni 2, Bucuresti",
    "items": [
        {"name": "VOPSEA LAVABILA ALBA SAVANA 15L", "um": "buc", "qty": 10, "price": 85.00},
        {"name": "VOPSEA EXTERIOR DANKE WEISS 10L", "um": "buc", "qty": 8, "price": 120.00},
        {"name": "LAC PARCHET POLICOLOR 2.5L", "um": "buc", "qty": 12, "price": 55.00},
        {"name": "TRAFALET ZUGRAVIT 25CM ROLA MIEL", "um": "buc", "qty": 20, "price": 15.50},
        {"name": "BANDA MASCARE TESA 50M GALBENA", "um": "buc", "qty": 30, "price": 8.90},
        {"name": "GLETIERA INOX 280MM MANER LEMN", "um": "buc", "qty": 10, "price": 22.00},
    ]
})

# Invoice 3: LEROY MERLIN - instalatii si electrice
create_invoice("factura_LEROYMERLIN_LM2026789.pdf", {
    "invoice_number": "LM 2026789",
    "date": "27.03.2026",
    "due_date": "26.04.2026",
    "supplier_name": "LEROY MERLIN ROMANIA S.R.L.",
    "supplier_cui": "19850320",
    "supplier_reg": "J40/7890/2010",
    "supplier_address": "Bd. Iuliu Maniu 546, Bucuresti",
    "items": [
        {"name": "TEAVA PPR 25MM PN20 4M", "um": "buc", "qty": 50, "price": 12.80},
        {"name": "COT PPR 90GR D25", "um": "buc", "qty": 100, "price": 2.50},
        {"name": "ROBINET SFERIC 1/2 BRASS", "um": "buc", "qty": 20, "price": 18.90},
        {"name": "CABLU ELECTRIC CYY 3X2.5MM 100M", "um": "buc", "qty": 5, "price": 280.00},
        {"name": "INTRERUPATOR SIMPLU LEGRAND NILOE ALB", "um": "buc", "qty": 30, "price": 12.50},
        {"name": "PRIZA DUBLA CU IMPAMANTARE LEGRAND", "um": "buc", "qty": 25, "price": 18.00},
        {"name": "BANDA IZOLATOARE NEAGRA 20M", "um": "buc", "qty": 50, "price": 3.50},
        {"name": "CLESTE PATENT 200MM CR-V", "um": "buc", "qty": 10, "price": 35.00},
        {"name": "CHEIE FIXA SET 6-22MM 8BUC", "um": "set", "qty": 5, "price": 65.00},
    ]
})

print(f"\nAll PDFs created in: {OUTPUT_DIR}")
print(f"Files: {os.listdir(OUTPUT_DIR)}")
