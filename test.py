from datadase.db import session
from services.db_updater import update_products_from_df
from services.load_ostatki import load_report

if __name__ == "__main__":
    df = load_report()
    print(update_products_from_df(df, session))
