from config import Config
import pandas as pd

df = pd.read_excel(Config.EXCEL_PATH)
print(df.head())