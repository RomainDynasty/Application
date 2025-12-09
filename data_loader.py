from api_bloomberg import BloombergDataFetcher
from logger_config import get_logger
import pandas as pd

#Initialisation du logger (gestion des erreurs)
logger = get_logger(__name__)

# Charger les donnnees 
class DataLoader:
    """Gestionnaire de chargement et fusion des données"""

    def __init__(self, config: dict):
        self.config = config
        self.bloomberg_fetcher = BloombergDataFetcher()
    
    def load_portfolio_data(self) -> pd.DataFrame:
        """Charge et fusionne toutes les données du portefeuille"""
        logger.info("Début du chargement des données")
        
        # Chargement des données principales
        df_port = self._load_portfolio_file()
        df_themes = self._load_themes_file()
        df_data = self._load_ovcv_data()
        df_ratings = self._load_internal_ratings()
        
        # Fusion des données
        df_merged = self._merge_all_data(df_port, df_themes, df_data, df_ratings)
        
        # Enrichissement avec Bloomberg
        df_enriched = self._enrich_with_bloomberg_data(df_merged)
        
        logger.info(f"Données chargées: {len(df_enriched)} lignes")
        return df_enriched
    
    def _load_portfolio_file(self) -> pd.DataFrame:
        """Charge le fichier principal du portefeuille"""
        try:
            df = pd.read_excel(self.config['files']['portfolio'], skiprows=3)
            logger.info(f"Fichier portefeuille chargé: {len(df)} lignes")
            return df
        except Exception as e:
            logger.error(f"Erreur chargement portefeuille: {e}")
            raise
    
    def _load_themes_file(self) -> pd.DataFrame:
        """Charge le fichier des thématiques"""
        try:
            df = pd.read_excel(self.config['files']['themes'])
            logger.info(f"Fichier thématiques chargé: {len(df)} lignes")
            return df
        except Exception as e:
            logger.error(f"Erreur chargement thématiques: {e}")
            raise
    
    def _load_ovcv_data(self) -> pd.DataFrame:
        """Charge les données OVCV"""
        try:
            df = pd.read_excel(self.config['files']['ovcv_data'], skiprows=6)
            
            # Colonnes à conserver
            colonnes_a_garder = [
                "Ticker", "Security Description", "Trade Date", "Bond Market Price",
                "Spread (Credit)", "Stock Volatility", "Volatility Spread",
                "Stock Price", "Bond Recovery (%)", "Borrow Cost (%)",
                "Future DVD Yield", "E2C Decay", "Greek Calculation Type",
                "Fair Value", "Implied Spread", "Implied Volatility",
                "Delta (%)", "Delta (pts)", "Gamma", "Vega", "Theta",
                "Cheapness (%)", "Soft Call Trigger", "Bond Floor",
                "Option Value", "Parity", "Premium (pts)", "Premium (%)",
                "Expected Life (Fugit)", "Interest Sensitivity",
                "Credit Sensitivity", "Convexity", "Effective Duration",
                "Yield to Mty", "Yield to Call", "Yield to Put",
                "Yield to Worst", "Current Yield"
            ]
            
            df = df[colonnes_a_garder]
            df["ISIN"] = df["Ticker"].str[:-5]
            
            logger.info(f"Données OVCV chargées: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur chargement OVCV: {e}")
            raise
    
    def _load_internal_ratings(self) -> pd.DataFrame:
        """Charge les ratings internes"""
        try:
            df = pd.read_excel(self.config['files']['internal_ratings'])
            df = df[["ISIN", "Rating", 'Rating Date']]
            df["Rating Date"] = pd.to_datetime(df["Rating Date"], errors="coerce")
            df = df.sort_values("Rating Date").drop_duplicates("ISIN", keep="last")
            
            logger.info(f"Ratings internes chargés: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"Erreur chargement ratings: {e}")
            raise
    
    def _merge_all_data(self, df_port: pd.DataFrame, df_themes: pd.DataFrame, 
                       df_data: pd.DataFrame, df_ratings: pd.DataFrame) -> pd.DataFrame:
        """Fusionne toutes les données"""
        logger.info("Début de la fusion des données")
        
        # Fusion avec les thématiques
        df_merged = df_port.merge(
            df_themes[["ISIN", "Theme"]],
            on="ISIN",
            how="left"
        )
        
        # Fusion avec les données OVCV
        df_merged = df_merged.merge(
            df_data,
            on="ISIN",
            how="left",
            suffixes=("", "_XCV")
        )
        
        # Fusion avec les ratings internes
        df_merged = df_merged.merge(
            df_ratings,
            on="ISIN",
            how="left",
            suffixes=("", "_Interne")
        )
        
        # Création du S&P ajusté
        df_merged["S&P Ajusted"] = df_merged["S&P"].fillna(df_merged["Rating"])
        
        logger.info("Fusion des données terminée")
        return df_merged
    
    def _enrich_with_bloomberg_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrichit les données avec les informations Bloomberg"""
        logger.info("Début de l'enrichissement Bloomberg")
        
        # Préparation des tickers equity
        mask_convertible = df['Security Type'] == 'Convertible Bonds'
        df.loc[mask_convertible, 'Eqty Ticker'] = df.loc[mask_convertible, 'Eqty Ticker'].astype(str) + ' Equity'
        
        # Récupération des tickers uniques non vides
        tickers_to_fetch = df[df['Eqty Ticker'].notna() & (df['Eqty Ticker'] != 'nan Equity')]['Eqty Ticker'].unique()
        
        if len(tickers_to_fetch) > 0:
            # Appel batch à Bloomberg
            bloomberg_data = self.bloomberg_fetcher.fetch_batch_data(
                list(tickers_to_fetch),
                ['EXPECTED_REPORT_DT', 'EXPECTED_REPORT_TIME']
            )
            
            # Application des résultats
            df['EXPECTED_REPORT_DT'] = df['Eqty Ticker'].map(
                lambda x: bloomberg_data.get(x, {}).get('EXPECTED_REPORT_DT') if x in bloomberg_data else None
            )
            df['EXPECTED_REPORT_TIME'] = df['Eqty Ticker'].map(
                lambda x: bloomberg_data.get(x, {}).get('EXPECTED_REPORT_TIME') if x in bloomberg_data else None
            )
        
        # Création de la colonne EARNING
        df["EARNING"] = df.apply(self._create_earning_column, axis=1)
        
        logger.info("Enrichissement Bloomberg terminé")
        return df
    
    def _create_earning_column(self, row) -> str:
        """Crée la colonne EARNING combinant date et heure"""
        if (pd.notna(row['EXPECTED_REPORT_TIME']) 
            and str(row['EXPECTED_REPORT_TIME']).strip().upper() != "#N/A N/A"
            and str(row['EXPECTED_REPORT_TIME']).strip() != ""):
            return f"{row['EXPECTED_REPORT_DT']} {row['EXPECTED_REPORT_TIME']}"
        else:
            return f"{row['EXPECTED_REPORT_DT']}"
    
    def close_bloomberg_connection(self):
        """Ferme la connexion Bloomberg"""
        self.bloomberg_fetcher.close_session()

