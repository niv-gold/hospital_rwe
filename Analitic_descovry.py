#%%
import pandas as pd
import numpy as np
import functools
import sqlite3
from sqlalchemy import create_engine

def error_handler(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise Exception(f'-->  function {func.__name__} failed, error msg: {e}')
    return wrap

@error_handler
def replace_col_names(df:pd.DataFrame, expression:str)->None:
    df.columns = ( df.columns
                    .str.lower()
                    .str.lower()
                    .str.replace('resource.','',regex=False))

@error_handler
def analitic_rank(df:pd.DataFrame)->pd.DataFrame:
    
    # -- spars rnak
    df = df.sort_values(['patient_id','period.start'],ascending=[True,True])
    # print(df[["patient_id","period.start","period.end","id"]].head(10).to_string())
    df['pat_enc_rnk'] = df.groupby("patient_id")["period.start"].rank(method='first').astype("int")
    df['is_enc_flag'] = np.select([df['pat_enc_rnk']<3, df['pat_enc_rnk']>3],['first_2','last_n'],'space')     
    df_res = df[df['pat_enc_rnk']<3].copy()
    cols = ["patient_id","period.start","period.end","id","pat_enc_rnk","is_enc_flag"]
    # print(df_res[cols].head(10).to_string())

    # -- dense rank --
    cols = ["patient_id","period.start","period.end","id","pat_enc_rnk","is_enc_flag","rnk_dense"]
    df = df.sort_values(['patient_id','period.start'],ascending=[True,True])
    df["rnk_dense"] = df.groupby('patient_id')['period.start'].rank(method='dense').astype("int")
    print(df[cols].head(10).to_string())

    # -- row number (deduplication index=1)
    cols = ["patient_id","period.start","period.end","id","pat_enc_rnk","is_enc_flag","rnk_dense","pat_rn"]
    df = df.sort_values(["patient_id","period.start"], ascending=[True,True])
    df["pat_rn"] = df.groupby("patient_id")["period.start"].rank(method="first").astype("int")
    print(df[cols].head(5).to_string())


@error_handler
def analitic_by_sum_by_M_Q_Y(df:pd.DataFrame)->None:
    cols = ["id", "patient_id", "period.start", "period.end", "pat_encout_YYYYQMM",
            "encounter_cost","pat_total_YYYYQ_exp","pat_total_YYYY_exp","pat_running_total_exp_YYYY"]
    np.random.seed(42)
    df["encounter_cost"] = np.random.randint(50,501,size=len(df))
    
    df.sort_values(["patient_id","period.start"],ascending=[True,True],inplace=True)
    df['pat_encout_YYYYQMM'] = (df["period.start"].dt.year*10 + df["period.start"].dt.quarter)*100 + \
                df["period.start"].dt.month
    df["pat_encout_YYYYQ"] = (df["pat_encout_YYYYQMM"]/100).astype("int")
    df["pat_encout_YYYY"] = df["period.start"].dt.year
    df["pat_total_M_exp"] = df.groupby(["patient_id","pat_encout_YYYYQMM"])["encounter_cost"].\
        transform("sum")
    df["pat_total_YYYYQ_exp"] = df.groupby(["patient_id","pat_encout_YYYYQ"])["encounter_cost"].transform(sum)
    df["pat_total_YYYY_exp"] = df.groupby(["patient_id","pat_encout_YYYY"])["encounter_cost"].transform(sum)
    df["pat_running_total_exp_YYYY"] = df.groupby(["patient_id","pat_encout_YYYY"])["encounter_cost"].cumsum()

    # print(df[cols].head(5).to_string())
    # print(df.info())

@error_handler
def analitic_leg_lead(df:pd.DataFrame)->None:
    df.sort_values(["patient_id","period.start"],ascending=[True,True], inplace=True)
    cols = ["id", "patient_id", "period.end","encounter_cost", "period.start", "previous_enc_date","next_enc_date"]
    df["previous_enc_date"] = df.groupby(["patient_id"])["period.start"].shift(1)
    df["next_enc_date"] = df.groupby(["patient_id"])["period.start"].shift(-1)
    # print(df[cols].head(10).to_string())

@error_handler
def analitic_rolling_window(df:pd.DataFrame)->None:
    # 3-encounter rolling sum
    cols = ["id", "patient_id", "period.end", "period.start", "previous_enc_date","next_enc_date", "encounter_cost", 
            "pat_expens_last_2_enc"]
    # min_periods ==> the minimum number of rows required to produce a result
    df["pat_expens_last_2_enc"] = df.groupby(["patient_id"])["encounter_cost"].\
                transform(lambda x: x.rolling(window=2, min_periods=1).sum())     
    # print(df[cols].head(20).to_string())

@error_handler
def analitic_expending_max(df:pd.DataFrame)->None:
    # expanding max — highest cost seen so far
    cols = ["id", "patient_id", "period.end", "period.start", "previous_enc_date","next_enc_date", 
            "encounter_cost", "pat_expending_expens","pat_expending_max"]
    df["pat_expending_expens"] = df.groupby(["patient_id"])["encounter_cost"].\
        transform(lambda x: x.expanding().sum())
    df["pat_expending_max"] = df.groupby(["patient_id"])["encounter_cost"].\
        transform(lambda x: x.expanding().max())
    # print(df[cols].head(20).to_string())


@error_handler
def analitic_expens_diff(df:pd.DataFrame)->None:
    # cost change between this and previous encounter per patient
    cols = ["id", "patient_id", "period.end", "period.start", "previous_enc_date","next_enc_date", 
            "encounter_cost", "pat_enc_expens_diff", "pat_enc_daydiff"]
    df["pat_enc_expens_diff"] = df.groupby(["patient_id"])["encounter_cost"].\
            transform(lambda x: x.diff())
    df["pat_enc_daydiff"] = df.groupby(["patient_id"])["period.start"].\
            transform(lambda x: x.diff())
    print(df[cols].head(20).to_string()) 

@error_handler
def analitic_ntile(df:pd.DataFrame)->None:
    # split encounters into 4 cost buckets per patient (NTILE(3))
    # The label is determined by where the value of the avaluated column falls in the 
    # distribution — not by row position. 
    cols = ["id", "patient_id", "period.end", "period.start", "previous_enc_date","next_enc_date", 
            "encounter_cost","pat_enc_3_tiles"]
    df["pat_enc_3_tiles"] = df.groupby(["patient_id"])["encounter_cost"].\
            transform(lambda x: pd.qcut(x, q=3, labels=[1,2,3], duplicates="drop"))
    print(df[cols].head(20).to_string())

@error_handler
def main():
    
    # ---- sql engine ----
    db_path = 'Data_files/sqlite_db'
    eng_bronze = create_engine(f'sqlite:///{db_path}/bronze.db')
    eng_silver = create_engine(f'sqlite:///{db_path}/silver.db')
    eng_gold = create_engine(f'sqlite:///{db_path}/gold.db')

    # ---- analitic quering ----

    df_data = pd.read_sql_table('stg_encounters', con=eng_silver)
    replace_col_names(df=df_data, expression='resource.')

    # analitic_rank(df=df_data)
    analitic_by_sum_by_M_Q_Y(df=df_data)
    analitic_leg_lead(df=df_data)
    analitic_rolling_window(df=df_data)
    analitic_expending_max(df=df_data)
    analitic_expens_diff(df=df_data)
    analitic_ntile(df=df_data)



#-----------------------------
if __name__=='__main__':
    main()

# %%
# 3-encounter rolling sum
df["cost_3enc_rolling_sum"] = (
    df.groupby("patient_id")["encounter_cost"]
      .transform(lambda x: x.rolling(window=3, min_periods=1).sum())
      
# expanding max — highest cost seen so far
)df["cost_expanding_max"] = (
    df.groupby("patient_id")["encounter_cost"]
      .transform(lambda x: x.expanding().max())
)

# cost change between this and previous encounter per patient
df["cost_change"] = (
    df.groupby("patient_id")["encounter_cost"]
      .diff()
)

# split encounters into 4 cost buckets per patient (NTILE(4))
df["cost_quartile"] = (
    df.groupby("patient_id")["encounter_cost"]
      .transform(lambda x: pd.qcut(x, q=4, labels=[1, 2, 3, 4], duplicates="drop"))
)

