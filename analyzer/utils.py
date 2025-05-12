from .models import Activity
import pandas as pd
import numpy as np
from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def log_activity(user, title, description, activity_type='info'):
    """
    Enregistre une activité dans le système
    """
    Activity.objects.create(
        user=user,
        title=title,
        description=description,
        type=activity_type
    )
    return True


def generate_pdf_report(prediction):
    """Génère un rapport PDF pour une prédiction"""
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Ajouter des styles personnalisés
    styles.add(ParagraphStyle(name='Title', 
                             parent=styles['Heading1'], 
                             alignment=TA_CENTER,
                             textColor=colors.HexColor('#7AAEB5')))
    
    styles.add(ParagraphStyle(name='Subtitle', 
                             parent=styles['Heading2'], 
                             alignment=TA_CENTER,
                             textColor=colors.HexColor('#5D8A91')))
    
    styles.add(ParagraphStyle(name='Normal_Center', 
                             parent=styles['Normal'], 
                             alignment=TA_CENTER))
    
    # Contenu du rapport
    elements = []
    
    # Titre
    elements.append(Paragraph("Rapport de Prédiction ROI", styles['Title']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Date
    elements.append(Paragraph(f"Date: {prediction.created_at.strftime('%d/%m/%Y')}", styles['Normal_Center']))
    elements.append(Spacer(1, 0.5*inch))
    
    # Résultat principal
    elements.append(Paragraph("Résultat de la prédiction", styles['Subtitle']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Tableau des résultats
    data = [
        ["ROI prédit", f"{prediction.roi:.2f}"],
        ["Type de campagne", prediction.get_campaign_type_display_name()],
        ["Canal utilisé", prediction.get_channel_used_display_name()],
        ["Taux de conversion", f"{prediction.conversion_rate:.2f}%"],
        ["Coût d'acquisition", f"{prediction.acquisition_cost:.2f}€"],
        ["Score d'engagement", f"{prediction.engagement_score:.1f}"],
        ["CTR", f"{prediction.ctr:.2f}%"],
        ["CPC", f"{prediction.cpc:.2f}€"]
    ]
    
    # Créer le tableau
    table = Table(data, colWidths=[2.5*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F4FD')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Interprétation
    elements.append(Paragraph("Interprétation", styles['Subtitle']))
    elements.append(Spacer(1, 0.25*inch))
    
    interpretation_text = f"Votre ROI prévu de {prediction.roi:.2f} indique "
    if prediction.roi >= 4:
        interpretation_text += "un excellent retour sur investissement pour votre campagne marketing."
    elif prediction.roi >= 2.5:
        interpretation_text += "un bon retour sur investissement pour votre campagne marketing."
    else:
        interpretation_text += "un retour sur investissement à améliorer pour votre campagne marketing."
    
    elements.append(Paragraph(interpretation_text, styles['Normal']))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph(f"Pour chaque euro investi, vous pouvez vous attendre à un retour de {prediction.roi:.2f} euros.", styles['Normal']))
    
    # Construire le PDF
    doc.build(elements)
    
    # Récupérer le contenu du PDF
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def export_dataset_to_csv(queryset):
    """Exporte un queryset de MarketingData en CSV"""
    # Créer un DataFrame pandas
    data = []
    for item in queryset:
        data.append({
            'Campaign_Type': item.campaign_type,
            'Channel_Used': item.channel_used,
            'Conversion_Rate': item.conversion_rate,
            'Acquisition_Cost': item.acquisition_cost,
            'ROI': item.roi,
            'Engagement_Score': item.engagement_score,
            'CTR': item.ctr,
            'CPC': item.cpc,
            'Date': item.created_at.strftime('%Y-%m-%d'),
            'Is_Prediction': item.is_prediction
        })
    
    df = pd.DataFrame(data)
    
    # Créer un buffer pour le CSV
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return csv_buffer.getvalue()
