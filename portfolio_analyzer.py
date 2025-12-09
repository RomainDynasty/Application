from logger_config import get_logger
import pandas as pd
import configparser
from data_loader import DataLoader
from portfolio_calculator import PortfolioCalculator
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

#Initialisation du logger (gestion des erreurs)
logger = get_logger(__name__)

class PortfolioAnalyzer:
    """Analyseur principal du portefeuille"""
    
    def __init__(self, config_path: str = "config.ini"):
        self.config = self._load_config(config_path)
        self.data_loader = DataLoader(self.config)
        self.calculator = PortfolioCalculator(self.config)
        self.df = None
    
    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis un fichier INI"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if not Path(config_path).exists():
            # Configuration par défaut si le fichier n'existe pas
            return {
                'files': {
                    'portfolio': os.path.join(script_dir,"DYN_CONV_PORT.xlsx"),
                    'themes': os.path.join(script_dir,"SPDR Thematique.xlsx"),
                    'ovcv_data': os.path.join(script_dir,"XCV_DYN_CONV_DATA_ONLY.xlsm"),
                    'internal_ratings': os.path.join(script_dir, "Rating_Interne.xlsx")
                },
                'output': {
                    'dir': script_dir,
                    'images_dir': script_dir
                },
                'settings': {
                    'fx_hedge_usd': 2.0, # passer en API later
                    'top_holdings': 10
                }
            }
        
        config = configparser.ConfigParser()
        config.read(config_path)
        return {
            'files': dict(config['files']),
            'output': dict(config['output']),
            'settings': {k: float(v) if k == 'fx_hedge_usd' else int(v) 
                        for k, v in config['settings'].items()}
        }
    
    def run_full_analysis(self) -> Dict[str, any]:
        """Exécute l'analyse complète du portefeuille"""
        logger.info("Début de l'analyse complète")
        
        try:
            # Chargement et calculs
            self.df = self.data_loader.load_portfolio_data()
            self.df = self.calculator.calculate_all_metrics(self.df)
            
            
            # Sauvegarder le DataFrame complet AVANT filtrage pour l'allocation par type d'actif
            self.df_complete = self.df.copy()
            
            
            # Filtrage des types de securities
            types_autorises = ["Convertible Bonds", "Common Stocks", "Warrants"]  
            self.df = self.df[self.df["Security Type"].isin(types_autorises)]
           
            
            # Calculs des métriques agrégées
            results = self._calculate_aggregated_metrics()
            
            logger.info("Analyse complète terminée")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            raise
        finally:
            # Fermeture de la connexion Bloomberg
            self.data_loader.close_bloomberg_connection()
        
    
    def _calculate_aggregated_metrics(self) -> Dict[str, any]:
        """Calcule toutes les métriques agrégées"""
        results = {}
        
        # Métriques principales
        results['holding'] = self.df["Security Type"].count()
        results['contrib_equity_sensi'] = self.df["CONTRIB SENSI EQUITY"].sum()
        results['contrib_equity_sensi_xcv'] = self.df["CONTRIB SENSI EQUITY XCV"].sum()
        results['premium'] = (self.df["% Prem"] * self.df["Market Value (%)"] / 100).sum()
        results['contrib_duration'] = self.df["OAD [cntr]"].sum()
        results['contrib_taux_sensi'] = self.df["contrib_taux_sensi"].sum()
        results['contrib_credit_sensi'] = self.df["contrib_credit_sensi"].sum()
        results['modified_duration'] = self.df["contrib_modified_duration"].sum()
        results['effective_duration'] = self.df["contrib_effective_duration"].sum()
        results['credit_analysis'] = self._calculate_credit_metrics()
        results['credit_spread'] = self.df["contrib_implied_spread"].sum()

        results['credit_analysis'] = self._calculate_credit_metrics()       
         
        # Rating final calculé par le PortfolioCalculator
        results['rating'] = self.calculator.rating_final
        
        
        # Top holdings
        results['top_10_holdings'] = self._get_top_holdings()
        results['top_10_contrib_equity'] = self._get_top_contributors()
        
        # Agrégations par secteur/région/thème/style
        results['contrib_by_sector'] = self._aggregate_by_sector()
        results['contrib_by_region'] = self._aggregate_by_region()
        results['contrib_by_theme'] = self._aggregate_by_theme()
        results['contrib_by_style'] = self._aggregate_by_style()
       
        # Buckets
        results['contrib_by_sensi_bucket'] = self._aggregate_by_sensi_bucket()
        results['contrib_by_vol_bucket'] = self._aggregate_by_vol_bucket()
        results['contrib_by_theme_name'] = self._aggregate_by_theme_name()
        
        return results
    
    def _get_top_holdings(self) -> pd.DataFrame:
        """Retourne le top 10 des holdings"""
        types_autorises = ["Convertible Bonds", "Corporate Bonds", "Open-End Funds", 
                          "Warrants", "Common Stocks"]
        df_filtered = self.df[self.df["Security Type"].isin(types_autorises)]
        
        top_10 = df_filtered.nlargest(self.config['settings']['top_holdings'], 
                                     "Market Value (%)")[["Long Name", "Short Name", "Market Value (%)"]]
        
        # Ajouter le total
        total_row = pd.DataFrame({
            "Long Name": ["TOTAL"],
            "Short Name": [""],
            "Market Value (%)": [top_10["Market Value (%)"].sum()]
        })
        
        return pd.concat([top_10, total_row], ignore_index=True).round(2)
    
    def _get_top_contributors(self) -> pd.DataFrame:
        """Retourne le top 10 des contributeurs equity"""
        top_10 = self.df.nlargest(self.config['settings']['top_holdings'], 
                                 "CONTRIB SENSI EQUITY")[["Long Name", "Short Name", "CONTRIB SENSI EQUITY"]]
        
        # Ajouter le total
        total_row = pd.DataFrame({
            "Long Name": ["TOTAL"],
            "Short Name": [""],
            "CONTRIB SENSI EQUITY": [top_10["CONTRIB SENSI EQUITY"].sum()],
            #"EARNING": [""]
        })
        
        return pd.concat([top_10, total_row], ignore_index=True).round(2)
    
    def _aggregate_by_sector(self) -> pd.DataFrame:
        """Agrège par secteur"""
        return (self.df.groupby("Industry Sector")["CONTRIB SENSI EQUITY"]
                .sum().reset_index().round(2)
                .sort_values("CONTRIB SENSI EQUITY", ascending=False))
    
    def _aggregate_by_region(self) -> pd.DataFrame:
        """Agrège par région"""
        return (self.df.groupby("REGION")["CONTRIB SENSI EQUITY"]
                .sum().reset_index().round(2)
                .sort_values("CONTRIB SENSI EQUITY", ascending=False))
    
    def _aggregate_by_theme(self) -> pd.DataFrame:
        """Agrège par thème"""
        return (self.df.groupby("Theme")["CONTRIB SENSI EQUITY"]
                .sum().reset_index().round(2)
                .sort_values("CONTRIB SENSI EQUITY", ascending=False))

    def _aggregate_by_style(self) -> pd.DataFrame:
        """Agrège par thème"""
        return (self.df.groupby("Style")["CONTRIB SENSI EQUITY"]
                .sum().reset_index().round(2)
                .sort_values("CONTRIB SENSI EQUITY", ascending=False))
    
    
    def _aggregate_by_sensi_bucket(self) -> pd.DataFrame:
        """Agrège par bucket de sensibilité"""
        return (self.df.groupby('SENSI BUCKET')
                .agg(Total_Contrib=('CONTRIB SENSI EQUITY', 'sum'),
                     Number_of_positions=('CONTRIB SENSI EQUITY', 'count'))
                .reset_index().round(2))
    
    def _aggregate_by_vol_bucket(self) -> pd.DataFrame:
        """Agrège par bucket de volatilité"""
        return (self.df.groupby('Vol_Bucket')
            
                .agg(Total_Contrib=('CONTRIB SENSI EQUITY', 'sum'),
                     Number_of_positions=('CONTRIB SENSI EQUITY', 'count'))
                .reset_index().round(2))

   
    def _aggregate_by_theme_name(self) -> pd.DataFrame:
        """Agrège par thème et nom"""
        # Filtrer les lignes avec contrib > 0.5
        filtre = self.df["CONTRIB SENSI EQUITY"] > 1
        df_filtre = self.df[filtre]
    
        return (
            df_filtre.groupby('Theme')[["Short Name", "CONTRIB SENSI EQUITY"]]
            .apply(lambda g: g.sort_values(
                by="CONTRIB SENSI EQUITY", ascending=False
            ))
            .round(2)
           )
                
    def _calculate_credit_metrics(self) -> Dict[str, pd.DataFrame]:
        """Calcule les métriques d'analyse crédit"""
        credit_results = {}
        
        # MODIFIÉ : Utiliser df_complete pour inclure Corporate Bonds et Cash
        # qui ont été exclus du self.df filtré
        df_credit = self.df_complete[
            self.df_complete["Security Type"].isin(["Corporate Bonds", "Convertible Bonds", "Cash"])
        ].copy()
        
        logger.info(f"Analyse crédit sur {len(df_credit)} lignes incluant Corporate Bonds, Convertible Bonds et Cash")
        
        # 1. Poids par catégorie IG/HY/Cash
        credit_results['by_category'] = (
            df_credit.groupby("Credit Category")
            .agg(
                Market_Value=('Market Value (%)', 'sum'),
                Number_of_positions=('Market Value (%)', 'count')
            )
            .reset_index()
            .round(2)
        )
        
        # 2. Poids par rating détaillé (exclure Cash pour cette vue)
        df_credit_rated = df_credit[df_credit["Security Type"] != "Cash"]
        poids_par_rating = (
            df_credit_rated.groupby("S&P Ajusted")
            .agg(
                Market_Value=('Market Value (%)', 'sum'),
                Number_of_positions=('Market Value (%)', 'count')
            )
            .reset_index()
            .round(2)
        )
        
        # Ordonner selon l'ordre S&P
        poids_par_rating["S&P Ajusted"] = pd.Categorical(
            poids_par_rating["S&P Ajusted"],
            categories=self.calculator.ordre_sp,
            ordered=True
        )
        credit_results['by_rating'] = poids_par_rating.sort_values("S&P Ajusted").reset_index(drop=True)
        
        # 3. Exposition par émetteur (Top 10) - exclure Cash
        credit_results['by_issuer'] = (
            df_credit_rated.groupby("Issuer")["Market Value (%)"]
            .sum()
            .reset_index()
            .sort_values(by="Market Value (%)", ascending=False)
            .round(2)
            .head(10)
        )
        
        # 4. Poids par bucket de maturité (inclure Cash qui sera dans <1 An)
        credit_results['by_maturity'] = (
            df_credit.groupby('Maturity_Bucket')
            .agg(
                Market_Value=('Market Value (%)', 'sum'),
                Number_of_positions=('Market Value (%)', 'count')
            )
            .reset_index()
            .round(2)
        )

        # Vue détaillée par bucket ET rating
        credit_results['by_maturity_rating'] = (
            df_credit.groupby(['Maturity_Bucket', 'S&P Ajusted'])
            .agg(
                Market_Value=('Market Value (%)', 'sum'),
                Number_of_positions=('Market Value (%)', 'count')
            )
            .reset_index()
            .round(2)
        )

        # Ordonner les ratings dans la vue détaillée
        credit_results['by_maturity_rating']["S&P Ajusted"] = pd.Categorical(
            credit_results['by_maturity_rating']["S&P Ajusted"],
            categories=self.calculator.ordre_sp + ['CASH'],
            ordered=True
        )
        credit_results['by_maturity_rating'] = credit_results['by_maturity_rating'].sort_values(
            ['Maturity_Bucket', 'S&P Ajusted']
        )

        logger.info("Métriques crédit calculées")

        return credit_results

    
