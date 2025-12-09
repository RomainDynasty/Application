import os 

class Config:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    EXCEL_PATH = os.path.join(script_dir, 'DYN_CONV_PORT.xlsx')

