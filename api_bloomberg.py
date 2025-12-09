# Bloomberg 
import numpy as np
import pandas as pd

from typing import Dict, List, Optional, Tuple
from logger_config import get_logger

logger = get_logger(__name__)


class BloombergDataFetcher:
    """Gestionnaire optimisé pour les appels Bloomberg API"""

    def __init__(self):
        self.session = None
        self.service = None
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialise la session Bloomberg"""
        try:
            from blpapi import SessionOptions, Session
            import blpapi
            
            options = SessionOptions()
            options.setServerHost('localhost')
            options.setServerPort(8194)
            
            self.session = Session(options)
            if not self.session.start():
                raise RuntimeError("Échec du démarrage de la session Bloomberg.")
            
            if not self.session.openService("//blp/refdata"):
                raise RuntimeError("Échec de l'ouverture du service Bloomberg.")
                
            self.service = self.session.getService("//blp/refdata")
            logger.info("Session Bloomberg initialisée avec succès")
            
        except ImportError:
            logger.error("Module blpapi non disponible")
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation Bloomberg: {e}")
            raise
    
    def fetch_batch_data(self, tickers: List[str], fields: List[str]) -> Dict[str, Dict[str, any]]:
        """
        Récupère les données pour plusieurs tickers en une seule requête
        
        Args:
            tickers: Liste des tickers Bloomberg
            fields: Liste des champs à récupérer
            
        Returns:
            Dictionnaire {ticker: {field: value}}
        """
        if not self.service or not tickers:
            return {}
        
        try:
            import blpapi
            
            request = self.service.createRequest("ReferenceDataRequest")
            
            # Ajouter tous les tickers
            for ticker in tickers:
                if ticker and str(ticker).strip():
                    request.getElement("securities").appendValue(str(ticker).strip())
            
            # Ajouter tous les champs
            for field in fields:
                request.getElement("fields").appendValue(field)
            
            self.session.sendRequest(request)
            
            results = {}
            
            while True:
                ev = self.session.nextEvent()
                
                for msg in ev:
                    if msg.messageType() == "ReferenceDataResponse":
                        security_data_array = msg.getElement("securityData")
                        
                        for i in range(security_data_array.numValues()):
                            security_data = security_data_array.getValueAsElement(i)
                            ticker = security_data.getElementAsString("security")
                            
                            results[ticker] = {}
                            
                            if security_data.hasElement("fieldData"):
                                field_data = security_data.getElement("fieldData")
                                
                                for field in fields:
                                    if field_data.hasElement(field):
                                        try:
                                            results[ticker][field] = field_data.getElementAsFloat(field)
                                        except:
                                            try:
                                                results[ticker][field] = field_data.getElementAsString(field)
                                            except:
                                                results[ticker][field] = None
                                    else:
                                        results[ticker][field] = None
                
                if ev.eventType() == blpapi.Event.RESPONSE:
                    break
            
            logger.info(f"Données récupérées pour {len(results)} tickers")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données Bloomberg: {e}")
            return {}
    
    def close_session(self):
        """Ferme la session Bloomberg"""
        if self.session:
            self.session.stop()
            logger.info("Session Bloomberg fermée")
