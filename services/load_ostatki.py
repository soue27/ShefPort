import pandas as pd

def load_report(path: str = "data/report.xls") -> pd.DataFrame:
    # Загружаем только нужные столбцы
    usecols = ["Код", "Цена продажи", "Количество"]
    df = pd.read_excel(path, usecols=usecols, dtype={"Код": str})
    df1 = df
    print(df)
    # Приводим поля "Код" и "Артикул" к строке
    df["Код"] = df["Код"].astype(str).str.strip()

    # Чистим типы
    df["Цена продажи"] = pd.to_numeric(df["Цена продажи"], errors="coerce").fillna(0)
    df["Количество"] = pd.to_numeric(df["Количество"], errors="coerce").fillna(0)


    print(df.info())
    return df





