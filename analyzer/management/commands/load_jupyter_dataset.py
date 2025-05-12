import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from analyzer.models import MarketingData

class Command(BaseCommand):
    help = 'Importe un dataset Jupyter (CSV ou Excel) dans la base de données Django'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Chemin vers le fichier CSV ou Excel')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        
        # Déterminer le type de fichier
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            self.stdout.write(self.style.ERROR('Format de fichier non supporté. Utilisez CSV ou Excel.'))
            return
        
        # Vérifier les colonnes requises
        required_columns = ['Campaign_Type', 'Channel_Used', 'Conversion_Rate', 
                           'Acquisition_Cost', 'ROI', 'Engagement_Score', 'CTR', 'CPC']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.stdout.write(self.style.ERROR(f'Colonnes manquantes: {", ".join(missing_columns)}'))
            return
        
        # Nettoyer les données
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        
        # Compter les lignes importées
        count = 0
        errors = 0
        
        # Importer les données
        for _, row in df.iterrows():
            try:
                MarketingData.objects.create(
                    campaign_type=int(row['Campaign_Type']),
                    channel_used=int(row['Channel_Used']),
                    conversion_rate=float(row['Conversion_Rate']),
                    acquisition_cost=float(row['Acquisition_Cost']),
                    roi=float(row['ROI']),
                    engagement_score=float(row['Engagement_Score']),
                    ctr=float(row['CTR']),
                    cpc=float(row['CPC']),
                    is_prediction=False
                )
                count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Erreur lors de l\'importation de la ligne: {e}'))
                errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'Importation réussie: {count} entrées ajoutées, {errors} erreurs'))
