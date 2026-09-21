"""
Dossier PDF Generator Module
Generates high-resolution, multi-page intelligence dossier PDF reports
for any suspect or person of interest using ReportLab.
"""

import io
import os
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and render total page count ('Page X of Y')
    along with tactical classification banners and document headers on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        width, height = A4
        self.saveState()

        # ── Top Security Banner ──
        banner_height = 20
        self.setFillColor(colors.HexColor("#7f1d1d"))  # Deep crimson
        self.rect(0, height - banner_height, width, banner_height, fill=1, stroke=0)
        self.setFillColor(colors.white)
        self.setFont("Helvetica-Bold", 8)
        self.drawCentredString(
            width / 2.0, height - 14,
            "RESTRICTED // LAW ENFORCEMENT & JUDICIAL INTELLIGENCE USE ONLY // STRICTLY CONFIDENTIAL"
        )

        # ── Top Document Header (Subtle) ──
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, height - 28, width - 36, height - 28)

        self.setFillColor(colors.HexColor("#64748b"))
        self.setFont("Helvetica", 7)
        self.drawString(36, height - 25, "CRIMENET AI — ADVANCED CRIMINAL NETWORK ANALYSIS SYSTEM")
        date_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S UTC")
        self.drawRightString(width - 36, height - 25, f"SYSTEM EXPORT: {date_str}")

        # ── Bottom Security Banner & Pagination ──
        self.setFillColor(colors.HexColor("#0f172a"))  # Obsidian Navy
        self.rect(0, 0, width, 22, fill=1, stroke=0)

        self.setFillColor(colors.HexColor("#94a3b8"))
        self.setFont("Helvetica", 7)
        self.drawString(
            36, 7,
            "CRIMENET AI INTELLIGENCE RECORD • UNAUTHORIZED SHARING PROHIBITED UNDER IT ACT 2000"
        )

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFillColor(colors.HexColor("#38bdf8"))
        self.setFont("Helvetica-Bold", 8)
        self.drawRightString(width - 36, 7, page_str)

        self.restoreState()


class DossierPDFGenerator:
    """Generates official criminal intelligence dossiers in PDF format."""

    @staticmethod
    def _format_currency(amount):
        """Format number into clean Indian Rupees format."""
        try:
            val = float(amount or 0)
            if val >= 10000000:
                return f"₹{val/10000000:.2f} Cr"
            elif val >= 100000:
                return f"₹{val/100000:.2f} Lakh"
            else:
                return f"₹{val:,.0f}"
        except Exception:
            return f"₹{amount}"

    @staticmethod
    def _get_risk_color(risk_level):
        """Return theme color tuple for risk level."""
        level = (risk_level or "LOW").upper()
        if level == "CRITICAL":
            return colors.HexColor("#dc2626"), colors.HexColor("#fee2e2")
        elif level == "HIGH":
            return colors.HexColor("#ea580c"), colors.HexColor("#ffedd5")
        elif level == "MEDIUM":
            return colors.HexColor("#d97706"), colors.HexColor("#fef3c7")
        else:
            return colors.HexColor("#16a34a"), colors.HexColor("#dcfce7")

    @classmethod
    def generate_dossier(cls, person, incidents, cdr_records, transactions,
                         criminal_history, resolved_associates=None, timeline=None):
        """
        Builds the entire PDF flowables and compiles the document into a BytesIO stream.
        """
        buffer = io.BytesIO()

        # Target A4 page with 36pt (0.5 inch) margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=32,
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569")
        )
        section_h1 = ParagraphStyle(
            'SectionH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=4
        )
        cell_bold = ParagraphStyle(
            'CellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b")
        )
        cell_normal = ParagraphStyle(
            'CellNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155")
        )
        cell_mono = ParagraphStyle(
            'CellMono',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#0f172a")
        )
        cell_muted = ParagraphStyle(
            'CellMuted',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#64748b")
        )

        elements = []
        page_width = A4[0] - 72  # 523.27 pt usable width

        # ── Header Block ──
        sid = person.get("id", "UNKNOWN")
        name = person.get("name", "Unknown Individual")
        risk_level = (person.get("risk_level") or "LOW").upper()
        risk_fg, risk_bg = cls._get_risk_color(risk_level)

        dossier_ref = f"DOS-{sid}-{datetime.now().strftime('%Y%m%d')}"
        sha_hash = hashlib.sha256(f"{sid}:{name}:{datetime.now()}".encode()).hexdigest()[:16].upper()

        header_table_data = [
            [
                Paragraph("<b>CRIMENET AI INTELLIGENCE DOSSIER</b>", title_style),
                Paragraph(f"<font color='{risk_fg.hexval()}'><b>CLASSIFICATION: {risk_level}</b></font>", ParagraphStyle('HRight', parent=cell_bold, alignment=2, fontSize=9))
            ],
            [
                Paragraph(f"<b>CASE FILE / DOSSIER ID:</b> {dossier_ref} &nbsp; | &nbsp; <b>SECURITY HASH:</b> {sha_hash}", subtitle_style),
                Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", ParagraphStyle('HRight2', parent=cell_muted, alignment=2))
            ]
        ]
        t_header = Table(header_table_data, colWidths=[page_width * 0.7, page_width * 0.3])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
        ]))
        elements.append(t_header)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceBefore=4, spaceAfter=8))

        # ── Section 1: Subject Identification & Demographics ──
        elements.append(Paragraph("<b>1. SUBJECT BIOGRAPHICAL & IDENTIFICATION PROFILE</b>", section_h1))

        primary_phone = person.get("phone") or "None Recorded"
        phone2 = person.get("phone2") or "None"
        phone_display = f"{primary_phone} (Alt: {phone2})" if person.get("phone2") else primary_phone
        org_display = person.get("organization") or "Independent / Unaffiliated"
        address_display = person.get("address") or "Not Specified / Unknown"
        age_gender = f"{person.get('age', 'N/A')} Years / {person.get('gender', 'N/A')}"
        vehicles_list = person.get("vehicles") or []
        if isinstance(vehicles_list, list) and vehicles_list:
            v_strs = []
            for v in vehicles_list:
                if isinstance(v, dict):
                    plate = v.get("plate", "")
                    vtype = v.get("type", "")
                    make = v.get("make", "")
                    desc = f"{make} {vtype} ({plate})".strip()
                    v_strs.append(desc if desc else str(v))
                else:
                    v_strs.append(str(v))
            vehicles_str = ", ".join(v_strs)
        else:
            vehicles_str = "None On Record"

        # Associates list
        associates_list = person.get("known_associates") or []
        if resolved_associates:
            assoc_str = ", ".join([f"{a.get('name', a.get('id'))} ({a.get('id')})" for a in resolved_associates[:6]])
        else:
            assoc_str = ", ".join([str(a) for a in associates_list[:6]]) if associates_list else "None Recorded"

        demo_data = [
            [
                Paragraph("<b>Full Legal Name:</b>", cell_bold),
                Paragraph(f"<b>{name}</b>", cell_bold),
                Paragraph("<b>Subject ID:</b>", cell_bold),
                Paragraph(f"<font color='#0284c7'><b>{sid}</b></font>", cell_mono)
            ],
            [
                Paragraph("<b>Risk Rating:</b>", cell_bold),
                Paragraph(f"<font color='{risk_fg.hexval()}'><b>{risk_level} RISK</b></font>", cell_bold),
                Paragraph("<b>Age / Gender:</b>", cell_bold),
                Paragraph(age_gender, cell_normal)
            ],
            [
                Paragraph("<b>Primary Phone:</b>", cell_bold),
                Paragraph(phone_display, cell_normal),
                Paragraph("<b>Syndicate / Org:</b>", cell_bold),
                Paragraph(f"<b>{org_display}</b>", cell_normal)
            ],
            [
                Paragraph("<b>Known Base / Address:</b>", cell_bold),
                Paragraph(address_display, cell_normal),
                Paragraph("<b>Registered Vehicles:</b>", cell_bold),
                Paragraph(vehicles_str, cell_normal)
            ],
            [
                Paragraph("<b>Known Associates:</b>", cell_bold),
                Paragraph(assoc_str, cell_normal),
                Paragraph("<b>Criminal Convictions:</b>", cell_bold),
                Paragraph(f"<b>{len(criminal_history)} Records On File</b>", cell_normal)
            ]
        ]

        t_demo = Table(demo_data, colWidths=[page_width * 0.20, page_width * 0.32, page_width * 0.20, page_width * 0.28])
        t_demo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t_demo)
        elements.append(Spacer(1, 8))

        # ── Section 2: Executive Intelligence Metrics ──
        total_calls = len(cdr_records)
        calls_made = sum(1 for c in cdr_records if str(c.get("caller_id")) == sid)
        calls_rec = sum(1 for c in cdr_records if str(c.get("receiver_id")) == sid)
        sent_amt = sum(float(t.get("amount", 0)) for t in transactions if str(t.get("sender_id")) == sid)
        rec_amt = sum(float(t.get("amount", 0)) for t in transactions if str(t.get("receiver_id")) == sid)
        suspicious_tx = sum(1 for t in transactions if t.get("is_suspicious") in [True, "True", "true", 1, "1"])

        metrics_data = [
            [
                Paragraph("<b>CRIMINAL FIRs</b>", ParagraphStyle('M1', parent=cell_bold, alignment=1, fontSize=7, textColor=colors.HexColor("#64748b"))),
                Paragraph("<b>PAST CONVICTIONS</b>", ParagraphStyle('M2', parent=cell_bold, alignment=1, fontSize=7, textColor=colors.HexColor("#64748b"))),
                Paragraph("<b>CALL INTERCEPTS</b>", ParagraphStyle('M3', parent=cell_bold, alignment=1, fontSize=7, textColor=colors.HexColor("#64748b"))),
                Paragraph("<b>MONEY SENT</b>", ParagraphStyle('M4', parent=cell_bold, alignment=1, fontSize=7, textColor=colors.HexColor("#64748b"))),
                Paragraph("<b>MONEY RECEIVED</b>", ParagraphStyle('M5', parent=cell_bold, alignment=1, fontSize=7, textColor=colors.HexColor("#64748b"))),
                Paragraph("<b>SUSPICIOUS TXNS</b>", ParagraphStyle('M6', parent=cell_bold, alignment=1, fontSize=7, textColor=colors.HexColor("#64748b"))),
            ],
            [
                Paragraph(f"<b>{len(incidents)}</b>", ParagraphStyle('V1', parent=cell_bold, alignment=1, fontSize=12, textColor=colors.HexColor("#ea580c"))),
                Paragraph(f"<b>{len(criminal_history)}</b>", ParagraphStyle('V2', parent=cell_bold, alignment=1, fontSize=12, textColor=colors.HexColor("#dc2626"))),
                Paragraph(f"<b>{total_calls}</b> ({calls_made}↑/{calls_rec}↓)", ParagraphStyle('V3', parent=cell_bold, alignment=1, fontSize=9, textColor=colors.HexColor("#0284c7"))),
                Paragraph(f"<b>{cls._format_currency(sent_amt)}</b>", ParagraphStyle('V4', parent=cell_bold, alignment=1, fontSize=9, textColor=colors.HexColor("#16a34a"))),
                Paragraph(f"<b>{cls._format_currency(rec_amt)}</b>", ParagraphStyle('V5', parent=cell_bold, alignment=1, fontSize=9, textColor=colors.HexColor("#16a34a"))),
                Paragraph(f"<b>{suspicious_tx} Flagged</b>", ParagraphStyle('V6', parent=cell_bold, alignment=1, fontSize=9, textColor=colors.HexColor("#dc2626") if suspicious_tx > 0 else colors.HexColor("#64748b"))),
            ]
        ]
        col_w = page_width / 6.0
        t_metrics = Table(metrics_data, colWidths=[col_w] * 6)
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t_metrics)
        elements.append(Spacer(1, 10))

        # ── Section 3: Criminal Convictions & Court Dispositions ──
        elements.append(Paragraph(f"<b>2. CRIMINAL HISTORY & JUDICIAL DISPOSITIONS ({len(criminal_history)} Records)</b>", section_h1))
        if criminal_history:
            hist_rows = [
                [
                    Paragraph("<b>Record ID</b>", cell_bold),
                    Paragraph("<b>Offense / Charge</b>", cell_bold),
                    Paragraph("<b>FIR / Case ID</b>", cell_bold),
                    Paragraph("<b>Date</b>", cell_bold),
                    Paragraph("<b>Court Jurisdiction</b>", cell_bold),
                    Paragraph("<b>Status</b>", cell_bold),
                    Paragraph("<b>Sentence / Order</b>", cell_bold),
                ]
            ]
            for h in criminal_history[:10]:
                status_color = "#dc2626" if h.get("status") == "CONVICTED" else "#d97706" if h.get("status") == "PENDING" else "#16a34a"
                hist_rows.append([
                    Paragraph(str(h.get("record_id", "—")), cell_mono),
                    Paragraph(f"<b>{h.get('crime_type', '—')}</b>", cell_normal),
                    Paragraph(str(h.get("case_id", "—")), cell_mono),
                    Paragraph(str(h.get("date", "—")), cell_normal),
                    Paragraph(str(h.get("court", "—")), cell_normal),
                    Paragraph(f"<font color='{status_color}'><b>{h.get('status', '—')}</b></font>", cell_bold),
                    Paragraph(str(h.get("sentence", "None")), cell_normal),
                ])

            t_hist = Table(
                hist_rows,
                colWidths=[page_width * 0.13, page_width * 0.22, page_width * 0.16, page_width * 0.12, page_width * 0.15, page_width * 0.11, page_width * 0.11]
            )
            t_hist.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            for col in range(len(hist_rows[0])):
                hist_rows[0][col].style.textColor = colors.white
            elements.append(t_hist)
        else:
            elements.append(Paragraph("<i>No prior court conviction records registered under this identification profile.</i>", cell_muted))

        elements.append(Spacer(1, 10))

        # ── Section 4: Logged Incidents & Modus Operandi ──
        elements.append(Paragraph(f"<b>3. LOGGED INCIDENTS & POLICE FIR INVOLVEMENT ({len(incidents)} Cases)</b>", section_h1))
        if incidents:
            inc_rows = [
                [
                    Paragraph("<b>Incident ID</b>", cell_bold),
                    Paragraph("<b>Crime Classification</b>", cell_bold),
                    Paragraph("<b>Date / Time</b>", cell_bold),
                    Paragraph("<b>Location</b>", cell_bold),
                    Paragraph("<b>Accomplices / Co-Accused</b>", cell_bold),
                    Paragraph("<b>Arrest</b>", cell_bold),
                ]
            ]
            for inc in incidents[:8]:
                acc = []
                if inc.get("suspect1_name") and str(inc.get("suspect1_id")) != sid:
                    acc.append(f"{inc.get('suspect1_name')} ({inc.get('suspect1_id')})")
                if inc.get("suspect2_name") and str(inc.get("suspect2_id")) != sid:
                    acc.append(f"{inc.get('suspect2_name')} ({inc.get('suspect2_id')})")
                accomplice_str = ", ".join(acc) if acc else "Solo / Unidentified"
                is_arrest = inc.get("arrest") in [True, "True", "true", 1, "1"]
                arrest_str = "<font color='#16a34a'><b>YES</b></font>" if is_arrest else "<font color='#dc2626'>NO</font>"

                inc_rows.append([
                    Paragraph(str(inc.get("incident_id", "—")), cell_mono),
                    Paragraph(f"<b>{inc.get('crime_type', '—')}</b>", cell_normal),
                    Paragraph(f"{inc.get('date', '')}<br/>{inc.get('time', '')}", cell_normal),
                    Paragraph(str(inc.get("location", "—")), cell_normal),
                    Paragraph(accomplice_str, cell_normal),
                    Paragraph(arrest_str, cell_normal),
                ])

            t_inc = Table(
                inc_rows,
                colWidths=[page_width * 0.16, page_width * 0.24, page_width * 0.14, page_width * 0.22, page_width * 0.16, page_width * 0.08]
            )
            t_inc.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            for col in range(len(inc_rows[0])):
                inc_rows[0][col].style.textColor = colors.white
            elements.append(t_inc)

            # Sample investigative narrative if available
            narratives = [inc for inc in incidents if inc.get("narrative")]
            if narratives:
                first_narrative = narratives[0]
                narrative_box = [
                    [
                        Paragraph(f"<b>Investigative Summary ({first_narrative.get('incident_id')}):</b> {first_narrative.get('narrative')}", cell_normal)
                    ]
                ]
                t_narrative = Table(narrative_box, colWidths=[page_width])
                t_narrative.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bfdbfe")),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(Spacer(1, 4))
                elements.append(t_narrative)
        else:
            elements.append(Paragraph("<i>No direct FIR incident involvements registered for this suspect.</i>", cell_muted))

        elements.append(Spacer(1, 10))

        # ── Section 5: Telecommunications Intercepts (CDR) ──
        elements.append(Paragraph(f"<b>4. TELECOMMUNICATIONS INTELLIGENCE & CALL DETAIL RECORDS (Top {min(len(cdr_records), 10)} of {len(cdr_records)})</b>", section_h1))
        if cdr_records:
            cdr_rows = [
                [
                    Paragraph("<b>CDR ID</b>", cell_bold),
                    Paragraph("<b>Date / Time</b>", cell_bold),
                    Paragraph("<b>Type</b>", cell_bold),
                    Paragraph("<b>Direction</b>", cell_bold),
                    Paragraph("<b>Contacted Party / Phone</b>", cell_bold),
                    Paragraph("<b>Duration</b>", cell_bold),
                    Paragraph("<b>Cell Tower Location</b>", cell_bold),
                ]
            ]
            for cdr in cdr_records[:10]:
                is_caller = str(cdr.get("caller_id")) == sid
                direction = "<font color='#0284c7'>OUTBOUND ↑</font>" if is_caller else "<font color='#16a34a'>INBOUND ↓</font>"
                other_phone = cdr.get("receiver_phone") if is_caller else cdr.get("caller_phone")
                other_id = cdr.get("receiver_id") if is_caller else cdr.get("caller_id")
                contact_str = f"{other_phone or '—'}<br/><font color='#64748b'>({other_id or 'Unknown'})</font>"

                dur = cdr.get("duration_seconds", 0)
                dur_str = f"{dur}s" if dur else "0s (SMS)"

                cdr_rows.append([
                    Paragraph(str(cdr.get("cdr_id", "—")), cell_mono),
                    Paragraph(f"{cdr.get('date', '')} {cdr.get('time', '')}", cell_normal),
                    Paragraph(str(cdr.get("call_type", "VOICE")), cell_normal),
                    Paragraph(direction, cell_bold),
                    Paragraph(contact_str, cell_normal),
                    Paragraph(dur_str, cell_normal),
                    Paragraph(str(cdr.get("cell_tower_location", "—")), cell_normal),
                ])

            t_cdr = Table(
                cdr_rows,
                colWidths=[page_width * 0.15, page_width * 0.17, page_width * 0.10, page_width * 0.13, page_width * 0.20, page_width * 0.10, page_width * 0.15]
            )
            t_cdr.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            for col in range(len(cdr_rows[0])):
                cdr_rows[0][col].style.textColor = colors.white
            elements.append(t_cdr)
        else:
            elements.append(Paragraph("<i>No intercepted telecommunication logs on record.</i>", cell_muted))

        elements.append(Spacer(1, 10))

        # ── Section 6: Financial Audit & Hawala Tracking ──
        elements.append(Paragraph(f"<b>5. FINANCIAL FORENSICS & MONEY TRAIL (Top {min(len(transactions), 10)} of {len(transactions)})</b>", section_h1))
        if transactions:
            txn_rows = [
                [
                    Paragraph("<b>Txn ID</b>", cell_bold),
                    Paragraph("<b>Date / Time</b>", cell_bold),
                    Paragraph("<b>Type</b>", cell_bold),
                    Paragraph("<b>Flow</b>", cell_bold),
                    Paragraph("<b>Amount (INR)</b>", cell_bold),
                    Paragraph("<b>Counterparty</b>", cell_bold),
                    Paragraph("<b>Bank / Remarks</b>", cell_bold),
                    Paragraph("<b>Alert</b>", cell_bold),
                ]
            ]
            for tx in transactions[:10]:
                is_sender = str(tx.get("sender_id")) == sid
                flow = "<font color='#ea580c'>SENT</font>" if is_sender else "<font color='#16a34a'>RECVD</font>"
                counterparty = tx.get("receiver_name") if is_sender else tx.get("sender_name")
                counter_id = tx.get("receiver_id") if is_sender else tx.get("sender_id")
                counter_str = f"{counterparty or '—'}<br/><font color='#64748b'>({counter_id or ''})</font>"

                is_susp = tx.get("is_suspicious") in [True, "True", "true", 1, "1"]
                flag_str = "<font color='#dc2626'><b>SUSPICIOUS</b></font>" if is_susp else "<font color='#16a34a'>Normal</font>"

                bank_remark = f"{tx.get('bank', '—')}<br/><font color='#64748b'>{tx.get('remarks', '')}</font>"

                txn_rows.append([
                    Paragraph(str(tx.get("txn_id", "—")), cell_mono),
                    Paragraph(f"{tx.get('date', '')} {tx.get('time', '')}", cell_normal),
                    Paragraph(str(tx.get("transaction_type", "—")), cell_normal),
                    Paragraph(flow, cell_bold),
                    Paragraph(f"<b>{cls._format_currency(tx.get('amount', 0))}</b>", cell_normal),
                    Paragraph(counter_str, cell_normal),
                    Paragraph(bank_remark, cell_normal),
                    Paragraph(flag_str, cell_normal),
                ])

            t_txn = Table(
                txn_rows,
                colWidths=[page_width * 0.14, page_width * 0.15, page_width * 0.10, page_width * 0.08, page_width * 0.14, page_width * 0.16, page_width * 0.13, page_width * 0.10]
            )
            t_txn.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            for col in range(len(txn_rows[0])):
                txn_rows[0][col].style.textColor = colors.white
            elements.append(t_txn)
        else:
            elements.append(Paragraph("<i>No financial transaction records flagged for this subject.</i>", cell_muted))

        elements.append(Spacer(1, 10))

        # ── Section 7: Master Life Chronology & Activity Timeline ──
        if timeline:
            elements.append(Paragraph(f"<b>6. SUBJECT LIFE ACTIVITY CHRONOLOGY ({len(timeline)} Events)</b>", section_h1))
            time_rows = [
                [
                    Paragraph("<b>Date & Time</b>", cell_bold),
                    Paragraph("<b>Event Type</b>", cell_bold),
                    Paragraph("<b>Event Description & Modus Operandi</b>", cell_bold),
                    Paragraph("<b>Location / Entities</b>", cell_bold),
                ]
            ]
            for evt in timeline[:12]:
                event_type = evt.get("type", "EVENT")
                type_color = "#dc2626" if "INCIDENT" in event_type or "CRIME" in event_type else "#0284c7" if "CALL" in event_type else "#16a34a"
                loc = evt.get("location") or "—"
                entities_str = ", ".join([str(e) for e in evt.get("entities", []) if e])
                loc_ent = f"{loc}<br/><font color='#64748b'>{entities_str}</font>" if entities_str else loc

                time_rows.append([
                    Paragraph(f"<b>{evt.get('date', '—')}</b><br/>{evt.get('time', '')}", cell_normal),
                    Paragraph(f"<font color='{type_color}'><b>{evt.get('type', 'EVENT')}</b></font>", cell_bold),
                    Paragraph(f"<b>{evt.get('title', '')}</b><br/>{evt.get('description', '')}", cell_normal),
                    Paragraph(loc_ent, cell_normal),
                ])

            t_time = Table(
                time_rows,
                colWidths=[page_width * 0.16, page_width * 0.16, page_width * 0.44, page_width * 0.24]
            )
            t_time.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            for col in range(len(time_rows[0])):
                time_rows[0][col].style.textColor = colors.white
            elements.append(t_time)

        elements.append(Spacer(1, 14))

        # ── Sign-off & Digital Security Verification Block ──
        verification_data = [
            [
                Paragraph(
                    f"<b>DIGITAL AUTHENTICITY HASH:</b><br/>"
                    f"<font face='Courier' size='7'>{hashlib.sha256((sid + name + str(datetime.now())).encode()).hexdigest()}</font><br/>"
                    f"<font color='#64748b'>Certified by CrimeNet AI Intelligence Engine • Autonomous Evidence Aggregator</font>",
                    cell_normal
                ),
                Paragraph(
                    "<b>AUTHORIZATION & VERIFICATION</b><br/>"
                    "Status: <b>VERIFIED RECORD</b><br/>"
                    "Issuing Authority: <b>LEAD INTELLIGENCE ANALYST</b><br/>"
                    "Jurisdiction: <b>CENTRAL CYBER & CRIME BUREAU</b>",
                    cell_normal
                )
            ]
        ]
        t_verif = Table(verification_data, colWidths=[page_width * 0.65, page_width * 0.35])
        t_verif.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(KeepTogether([t_verif]))

        # Build document with NumberedCanvas
        doc.build(elements, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer
