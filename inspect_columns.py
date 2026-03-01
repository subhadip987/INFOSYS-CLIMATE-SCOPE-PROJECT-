import pandas as pd

path = r"c:\Users\SUBHADIP MANDAL\OneDrive\Desktop\Milestone 2 ClimateScope Project\GlobalWeatherRepository.csv"
df = pd.read_csv(path)
print(df.columns)
print(df.head())
