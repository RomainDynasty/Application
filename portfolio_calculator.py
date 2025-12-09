import pandas as pd
from logger_config import get_logger

#Initialisation du logger (gestion des erreurs)
logger = get_logger(__name__)

class PortfolioCalculator:
    """Calculateur des métriques de portefeuille"""
 
    def __init__(self, config: dict):
        self.config = config
        self.sp_rating_to_number = {
            "AAA": 1, "AA+": 2, "AA": 3, "AA-": 4, "A+": 5, "A": 6, "A-": 7,
            "BBB+": 8, "BBB": 9, "BBB-": 10, "BB+": 11, "BB": 12, "BB-": 13,
            "B+": 14, "B": 15, "B-": 16, "CCC+": 17, "CCC": 18, "CCC-": 19,
            "CC": 20, "C": 21, "D": 22
        }

       
        self.ordre_sp = [
            "AAA", "AAA-", "AA+", "AA", "AA-", "A+", "A", "A-", 
            "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", 
            "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D", "NR"
        ]
        
        
        self.ig_ratings = ["AAA", "AAA-", "AA+", "AA", "AA-", "A+", "A", "A-", 
                          "BBB+", "BBB", "BBB-"]
        

        
        self.delta_par_defaut = {
            "Common Stocks": 1, "Corporate Bonds": 0, "Currency Forwards": 0,
            "Open-End Funds": 0, "Warrants": 1, "Cash": 0
        }
        
        self.pays_vers_region = {
            "BE": "Europe", "CA": "America", "CN": "Asia Ex-Jap", "DE": "Europe",
            "ES": "Europe", "FR": "Europe", "GB": "Europe", "IT": "Europe",
            "KR": "Asia Ex-Jap", "LU": "Europe", "MX": "Others", "NL": "Europe",
            "NZ": "Asia Ex-Jap", "TW": "Asia Ex-Jap", "US": "America",
            "EU": "Europe", "HK": "Asia Ex-Jap", "JP": "Japan", "CH": "Europe"
        }


        self.Sector_vers_Style = {
            "Technology": "Growth",
            "HealthCare": "Growth",
            "Communications": "Growth",
            "Basic Materials": "Cyclical",
            "Industrial": "Cyclical",
            "Energy": "Cyclical",
            "Consumer, Cyclical": "Cyclical",
            "Financial": "Value",
            "Utilities": "Value",
            "Consumer, Non-cyclical": "Value",
        }
    

    
    
    def calculate_all_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule toutes les métriques du portefeuille"""
        logger.info("Début des calculs de métriques")
        
        df = df.copy()
        
        # Applications des corrections manuelles
        df = self._apply_manual_corrections(df)
        
        # Calculs des ratings
        df = self._calculate_ratings(df)
        
        # Calculs des sensibilités
        df = self._calculate_sensitivities(df)
        
        # Calculs des buckets
        df = self._calculate_buckets(df)
        
        # Calculs des régions
        df = self._calculate_regions(df)

         # Calculs des asset types
        df = self._calculate_asset(df)

         # Calculs des styles
        df = self._calculate_style(df)

         # Calculs des buckets de maturity
        df = self._calculate_maturity_buckets(df)

        
    
        logger.info("Calculs de métriques terminés")
        return df

    
    def _apply_manual_corrections(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applique les corrections manuelles spécifiques"""
        # Corrections pour des ISIN spécifiques
        df.loc[df['ISIN'] == 'US06744EDH71', ['Short Name', 'Sector', 'Cntry (Risk)']] = ['MICROSOFT', 'Technology', 'US']
        df.loc[df['ISIN'] == 'US06744EDH71', 'Eqty Ticker'] = 'MSFT US'
        df.loc[df['ISIN'] == 'US29446YAC03', 'Eqty Ticker'] = 'EQX US'
        df.loc[df['ISIN'].isin(['FR001400R1R6', 'FR001400M9F9']), 'Cntry (Risk)'] = 'FR'

        return df

    def _is_valid_rating(self, val) -> bool:
        """Vérifie si une valeur de rating est valide"""
        if pd.isna(val):
            return False
        val_str = str(val).strip().upper()
        return val_str not in ["", "NR", "#N/A", "NAN", "NONE"]
    
    def _assign_rating_improved(self, row) -> str:
        """Assigne un rating en suivant une logique de priorité robuste"""
        # Priorité 1 : S&P
        if self._is_valid_rating(row["S&P"]):
            return str(row["S&P"]).strip()
        
        # Priorité 2 : S&P LT Foreign Currency
        if "S&P LT Foreign Currency Issuer Credit Rating" in row.index:
            if self._is_valid_rating(row["S&P LT Foreign Currency Issuer Credit Rating"]):
                return str(row["S&P LT Foreign Currency Issuer Credit Rating"]).strip()
        
        # Priorité 3 : Rating interne
        if self._is_valid_rating(row["Rating"]):
            return str(row["Rating"]).strip()
        
        return "NR"

    
    def _calculate_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les métriques liées aux ratings"""
        
        # Diagnostic AVANT traitement
        logger.info("=== DIAGNOSTIC RATINGS AVANT TRAITEMENT ===")
        logger.info(f"S&P uniques: {df['S&P'].value_counts(dropna=False).to_dict()}")
        
        # Application de la logique améliorée
        df['S&P Ajusted'] = df.apply(self._assign_rating_improved, axis=1)

        #  Assigner un rating spécial "CASH" aux liquidités
        df.loc[df['Security Type'] == 'Cash', 'S&P Ajusted'] = 'CASH'
        
        # Diagnostic APRÈS traitement
        logger.info("=== APRÈS CORRECTION ===")
        logger.info(f"S&P Ajusted uniques: {df['S&P Ajusted'].value_counts().to_dict()}")
        
        # Identifier les ISIN avec NR
        isin_nr = df[df["S&P Ajusted"] == "NR"]["ISIN"].tolist()
        if len(isin_nr) > 0:
            logger.warning(f"{len(isin_nr)} ISIN restent avec NR")
            detail_nr = df[df["S&P Ajusted"] == "NR"][
                ["ISIN", "Long Name", "S&P", "Rating", "S&P Ajusted"]
            ]
            logger.debug(f"Détail NR:\n{detail_nr}")
        
        
        df['Rating Chiffre'] = df['S&P Ajusted'].map(self.sp_rating_to_number)
        
        """df['Credit Category'] = df['S&P Ajusted'].apply(
            lambda x: 'Investment Grade' if x in self.ig_ratings else 
                     ('High Yield' if x not in ['NR', 'D'] else 'Not Rated')
        )"""

        df['Credit Category'] = df.apply(
            lambda row: 'Cash' if row['Security Type'] == 'Cash' 
            else ('Investment Grade' if row['S&P Ajusted'] in self.ig_ratings 
              else ('High Yield' if row['S&P Ajusted'] not in ['NR', 'D'] 
                    else 'Not Rated')),
            axis=1
        )
        
        # Filtrer pour le calcul du rating du fonds
        df_filtre = df[df["Security Type"].isin(["Corporate Bonds", "Convertible Bonds"])].copy()
        df_filtre["Contrib Rating Chiffre"] = (
            df_filtre['Rating Chiffre'] * df_filtre["Market Value (%)"] / 100
        )
        
        rating_chiffre = df_filtre["Contrib Rating Chiffre"].sum()
        number_to_sp_rating = {v: k for k, v in self.sp_rating_to_number.items() if v != 99}
        closest_number = min(number_to_sp_rating.keys(), key=lambda x: abs(x - rating_chiffre))
        self.rating_final = number_to_sp_rating[closest_number]
        
        logger.info(f"Rating S&P du fonds: {self.rating_final}")
        
        return df

    def _calculate_maturity_buckets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les buckets de maturité pour l'analyse crédit"""
        df['Years to Mat'] = df.apply(
        lambda row: 0.003 if row['Security Type'] == 'Cash' else row['Years to Mat'],
        axis=1
        )
        
        bins_mat = [float('-inf'), 1, 3, 5, float('inf')]
        labels_mat = ['<1 An', '1 à 3 Ans', '3 à 5 Ans', '>5 Ans']
        df['Maturity_Bucket'] = pd.cut(
            df['Years to Mat'], bins=bins_mat, labels=labels_mat, right=False
        )
        return df 
            
    

    def _calculate_sensitivities(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule toutes les sensibilités"""
        
        # Sensibilité Equity
        df["Delta"] = df.apply(
            lambda row: self.delta_par_defaut.get(row["Security Type"], row["Delta"]) 
            if pd.isna(row["Delta"]) else row["Delta"],
            axis=1
        )
        
        df["SENSI EQUITY"] = df["Delta"] / (1 + (df["% Prem"] / 100))
        df["CONTRIB SENSI EQUITY"] = (
            df["SENSI EQUITY"].fillna(0) * df["Market Value (%)"].fillna(0)
        )
        
        # Sensibilité Equity XCV
        df["Delta (%)"] = df.apply(
            lambda row: self.delta_par_defaut.get(row["Security Type"], row["Delta (%)"]) 
            if pd.isna(row["Delta (%)"]) else row["Delta (%)"],
            axis=1
        )
        
        df["SENSI EQUITY XCV"] = df["Delta (%)"] / (1 + (df["Premium (%)"] / 100))
        df["CONTRIB SENSI EQUITY XCV"] = (
            df["SENSI EQUITY XCV"].fillna(0) * df["Market Value (%)"].fillna(0)
        )
        
        # Agrégation Duration du fonds
        df["contrib_modified_duration"] = ( df["Mod Dur to Worst"] *df["Market Value (%)"] / 100 )
        
        # Agrégation  Effective Duration via XCV
        # Step 1 : Remplacer les valeurs manquantes pour les non-convertibles
        df["Effective Duration"] = df.apply(
            lambda row: row["Mod Dur to Worst"]   if row["Security Type"] != "Convertible Bonds" else row["Effective Duration"],
            axis=1
        )
        #step 2 : calculer la contrib
        df["contrib_effective_duration"] = ( df["Effective Duration"] * df["Market Value (%)"] / 100 )
        
        
        # Sensibilité Taux
        df["Interest Sensitivity"] = df.apply(
            lambda row: (row["OAD"] * -1) if row["Security Type"] != "Convertible Bonds" 
            else row["Interest Sensitivity"], axis=1
        )
        
        df["contrib_taux_sensi"] = (
            df["Interest Sensitivity"] * df["Market Value (%)"] / 100
        )
        
        # Sensibilité Crédit 
        df["Credit Sensitivity"] = df.apply(
            lambda row: (row["OAC"] * -1) if row["Security Type"] != "Convertible Bonds" 
            else row["Credit Sensitivity"], axis=1
        )
        
        df["contrib_credit_sensi"] = (
            df["Credit Sensitivity"] * df["Market Value (%)"] / 100
        )

        df["contrib_implied_spread"] = ( df["Implied Spread"] * df["Market Value (%)"] / 100 )
          
        return df
    
    def _calculate_buckets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les buckets (sensibilité, volatilité, maturité)"""
        # Buckets de sensibilité equity
        bins_equity = [0, 0.25, 0.50, 0.75, 1.1]
        labels_equity = ["Bucket 0-25", "Bucket 25-50", "Bucket 50-75", "Bucket 75-100"]
        df["SENSI BUCKET"] = pd.cut(
            df["SENSI EQUITY"], bins=bins_equity, labels=labels_equity, include_lowest=True
        )
        
        # Buckets de volatilité
        bins_vol = [float('-inf'), 20, 30, 40, float('inf')]
        labels_vol = ['<20%', '20-30%', '30-40%', '>40%']
        df['Vol_Bucket'] = pd.cut(
            df['Implied Volatility'], bins=bins_vol, labels=labels_vol, right=False
        )
        
        # Buckets de maturité
        bins_mat = [float('-inf'), 1, 3, 5, float('inf')]
        labels_mat = ['<1 An', '1 à 3 Ans', '3 à 5 Ans', '>5 Ans']
        df['Maturity_Bucket'] = pd.cut(
            df['Years to Mat'], bins=bins_mat, labels=labels_mat, right=False
        )
        
        return df
    
    def _calculate_regions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les régions à partir des pays"""
        df["REGION"] = df["Cntry (Risk)"].map(self.pays_vers_region)
        
        # Vérifier les codes non mappés
        codes_non_reconnus = df[df["REGION"].isna()]["Cntry (Risk)"].unique()
        if len(codes_non_reconnus) > 0:
            logger.warning(f"Pays non mappés: {codes_non_reconnus}")
        
        return df

    def _calculate_asset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les asset types"""
        contrib_by_security = df.groupby("Security Type")["Market Value (%)"].sum().reset_index().round(2)

        return df

    def _calculate_style(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les styles à partir des secteurs"""
        df["Style"] = df["Industry Sector"].map(self.Sector_vers_Style)
        
        # Vérifier les codes non mappés
        codes_non_reconnus = df[df["Style"].isna()]["Industry Sector"].unique()
        if len(codes_non_reconnus) > 0:
            logger.warning(f"Pays non mappés: {codes_non_reconnus}")
        
        return df
