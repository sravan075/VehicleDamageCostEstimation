"""
PDF bill generation service
"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import base64
from PIL import Image as PILImage

def generate_detailed_bill(results, car_model):
    """
    Generate a detailed PDF bill with results and invoice
    
    Args:
        results: list of detection results
        car_model: str, car model name
        
    Returns:
        BytesIO: PDF buffer
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    elements = []
    
    # Header section
    elements.append(Paragraph("REPAIR ESTIMATE", title_style))
    elements.append(Paragraph("Vehicle Damage Assessment", subtitle_style))
    
    # Metadata
    meta_data = [
        ['Date:', datetime.now().strftime('%d %B %Y')],
        ['Vehicle:', car_model],
        ['Images Analyzed:', str(len(results))]
    ]
    meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))
    
    # Results section
    elements.append(Paragraph("Detection Results", heading_style))
    
    for i, result in enumerate(results):
        if "cost_estimate" in result:
            # Add result details
            result_data = [
                ['Image:', f"{result.get('imageIndex', i+1)} - {result.get('imageName', 'Unknown')}"],
                ['Damage Type:', result['damage']],
                ['Severity:', result['severity']],
                ['Repair Cost:', f"₹{result['cost_estimate']['Total Repair Cost']:,}"]
            ]
            
            result_table = Table(result_data, colWidths=[2*inch, 4*inch])
            result_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7f8c8d')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f5e9')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
            ]))
            elements.append(result_table)
            
            # Try to add image if available
            try:
                if 'labeled_image' in result:
                    img_data = base64.b64decode(result['labeled_image'])
                    img_buffer = BytesIO(img_data)
                    pil_img = PILImage.open(img_buffer)
                    
                    # Save to temp buffer for reportlab
                    temp_img_buffer = BytesIO()
                    pil_img.save(temp_img_buffer, format='JPEG')
                    temp_img_buffer.seek(0)
                    
                    # Add image with limited size
                    img = PILImage.open(temp_img_buffer)
                    aspect = img.height / float(img.width)
                    img_width = 4.5*inch
                    img_height = img_width * aspect
                    
                    if img_height > 3*inch:
                        img_height = 3*inch
                        img_width = img_height / aspect
                    
                    rl_image = RLImage(temp_img_buffer, width=img_width, height=img_height)
                    elements.append(Spacer(1, 10))
                    elements.append(rl_image)
            except:
                pass
            
            elements.append(Spacer(1, 20))
    
    # Invoice section
    elements.append(Paragraph("Cost Breakdown & Invoice", heading_style))
    elements.append(Spacer(1, 10))
    
    # Calculate totals
    total_painting = sum(r['cost_estimate']['Painting Cost'] for r in results if 'cost_estimate' in r)
    total_labour = sum(r['cost_estimate']['Labour Cost'] for r in results if 'cost_estimate' in r)
    total_parts = sum(r['cost_estimate']['Part Price'] for r in results if 'cost_estimate' in r)
    total_components = sum(r['cost_estimate']['Component Price'] for r in results if 'cost_estimate' in r)
    total_internal = sum(r['cost_estimate']['Internal Damage Cost'] for r in results if 'cost_estimate' in r)
    subtotal = sum(r['cost_estimate']['Total Repair Cost'] for r in results if 'cost_estimate' in r)
    gst = subtotal * 0.18
    grand_total = subtotal + gst
    
    # Invoice table
    invoice_data = [
        ['Description', 'Qty', 'Amount (₹)'],
        ['Painting Cost', str(len(results)), f'{total_painting:,}'],
        ['Labour Cost', str(len(results)), f'{total_labour:,}'],
        ['Part Replacement', str(sum(1 for r in results if r['cost_estimate']['Part Price'] > 0)), f'{total_parts:,}'],
        ['Component Replacement', str(sum(1 for r in results if r['cost_estimate']['Component Price'] > 0)), f'{total_components:,}'],
        ['Internal Damage Repair', str(sum(1 for r in results if r['cost_estimate']['Internal Damage Cost'] > 0)), f'{total_internal:,}'],
        ['', 'Subtotal', f'₹{subtotal:,}'],
        ['', 'GST (18%)', f'₹{gst:,.2f}'],
        ['', 'TOTAL AMOUNT', f'₹{grand_total:,.2f}'],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[3.5*inch, 1*inch, 1.5*inch])
    invoice_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Body
        ('FONTNAME', (0, 1), (-1, 5), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 5), 10),
        ('TEXTCOLOR', (0, 1), (-1, 5), colors.HexColor('#2c3e50')),
        ('GRID', (0, 0), (-1, 5), 0.5, colors.HexColor('#ecf0f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, 5), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 1), (-1, 5), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 5), 8),
        
        # Subtotal
        ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 6), (-1, 6), 10),
        ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 6), (-1, 6), 8),
        ('BOTTOMPADDING', (0, 6), (-1, 6), 8),
        ('LINEABOVE', (0, 6), (-1, 6), 1, colors.HexColor('#bdc3c7')),
        
        # GST
        ('FONTNAME', (0, 7), (-1, 7), 'Helvetica'),
        ('FONTSIZE', (0, 7), (-1, 7), 10),
        ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 7), (-1, 7), 8),
        ('BOTTOMPADDING', (0, 7), (-1, 7), 8),
        
        # Total
        ('BACKGROUND', (0, 8), (-1, 8), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 8), (-1, 8), colors.whitesmoke),
        ('FONTNAME', (0, 8), (-1, 8), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 8), (-1, 8), 12),
        ('TOPPADDING', (0, 8), (-1, 8), 12),
        ('BOTTOMPADDING', (0, 8), (-1, 8), 12),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 20))
    
    # Footer note
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("<strong>Note:</strong> This is an estimated cost. Final charges may vary based on actual repair requirements.", note_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

