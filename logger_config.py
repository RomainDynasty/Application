import logging

def setup_logging():
    """Configure le logging pour toute l'application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_logger(name):
    """Retourne un logger pour un module spécifique"""
    return logging.getLogger(name)