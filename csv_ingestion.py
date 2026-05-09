
#%%
#=========================================================
# Import Block
#=========================================================
import pandas as pd
import numpy as np
import functools
from functools import reduce
import logging

#=========================================================
# Local Variable Block
#=========================================================

SCHEMA = {
    'col': 'encounter_id', 'data_type': str,
    'col': 'patient_id', 'data_type': str,
    'col': 'patient_name', 'data_type': str,
    'col': 'birth_date', 'data_type': str,
    'col': 'gender', 'data_type': str,
    'col': 'phone', 'data_type': str,
    'col': 'zip_code', 'data_type': int,
    'col': 'insurance_type', 'data_type': str,
    'col': 'smoking_status', 'data_type': str,
    'col': 'encounter_type', 'data_type': str,
    'col': 'department', 'data_type': str,
    'col': 'admit_date', 'data_type': str,
    'col': 'discharge_date', 'data_type': str,
    'col': 'length_of_stay_days', 'data_type': int,
    'col': 'attending_physician_id', 'data_type': str,
    'col': 'attending_physician_name', 'data_type': str,
    'col': 'primary_diagnosis_code', 'data_type': str,
    'col': 'primary_diagnosis_desc', 'data_type': str,
    'col': 'secondary_diagnosis_code', 'data_type': str,
    'col': 'secondary_diagnosis_desc', 'data_type': str,
    'col': 'medication_name', 'data_type': str,
    'col': 'medication_dosage', 'data_type': str,
    'col': 'lab_test_name', 'data_type': str,
    'col': 'lab_result_value', 'data_type': str,
    'col': 'lab_result_unit', 'data_type': str,
    'col': 'lab_reference_range', 'data_type': str,
    'col': 'bmi', 'data_type': str,
    'col': 'notes', 'data_type': str
}


#=========================================================
# Functions Block
#=========================================================

def profiling(df:pd.DataFrame, df_name:str)-> None:
    print('== df info ==')
    print(df.info())
    print('== df sample ==')
    print(df.head(5).to_string())
    print('== fd nolls ==')
    print (df.isnull().sum())

# Transformation - cleansing and data alignment (no busness dependencies)
def pipe_error_handler(func):
    @functools.wraps(func)
    def weraper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{func.__name__} error: {e}")
            raise Exception(f"--> Function '{func.__name__}()' error: {e} !!!")
    return weraper


@pipe_error_handler
def dead_letter_queue(df:pd.DataFrame, key_columns:list[str])->pd.DataFrame:
    ''' seperate quarntine rows from the rest ingest data'''

    conditions = [df[col].isnull() for col in key_columns]
    mask = reduce(lambda x,y: x|y, conditions)
    df_valid = df[~mask].copy()
    df_DLQ = df[mask].copy()
    return df_valid, df_DLQ 


@pipe_error_handler
def df_column_strip(df:pd.DataFrame)-> pd.DataFrame:
    # TBD: strip, lowercase , Add a @decorator wraper for logging and raise error for all funcitons!
    columns = df.columns
    df_str_col = [col for col in columns if df[col].apply( lambda x: isinstance(x,str)).all()]
    for col in df_str_col:
        df[col] = df[col].str.strip()
    
    return df
@pipe_error_handler
def date_iso_all(df:pd.DataFrame)->pd.DataFrame:
    lst_col_dt = [col for col in df.columns 
                            if any(sub in col.lower() for sub in ['date','period'])
                        ]
    for col in lst_col_dt:
        df_iso_col = date_iso(df=df,col=col)
    return df_iso_col
    
@pipe_error_handler
def date_iso(df:pd.DataFrame, col:str)->pd.DataFrame:
    'alinging all data format into the universal YYYY-MM-DD'
    col_dt_iso = f'{col}_iso'
    df[col_dt_iso] = pd.to_datetime(df[col], errors='coerce', format=None)
    df_iso = is_date_iso_embigues(df=df, col=col_dt_iso)
    return df_iso
    
@pipe_error_handler
def is_date_iso_embigues(df:pd.DataFrame, col:str)->pd.DataFrame:
    df[f'{col}_is_mbg'] = np.where((df[col].dt.day <= 12) & (df[col].dt.month <= 12),1,0)
    return(df)

@pipe_error_handler
def schema_enforement(df:pd.DataFrame, schema:dict)->pd.DataFrame:

    cast_column_fix(df=df, col='encounter_id', data_type=str)


@pipe_error_handler
def cast_column_fix(df:pd.DataFrame, col:str, data_type:type)->pd.DataFrame:
    
    df[col] =  df[col].astype(str).where(df[col].notna(), None)
    res = df[col].apply(lambda x: isinstance(x,str)).all()
    print(f'--> Check column "{col}" data valid {data_type}: {res}')




#=========================================================
# Running Block - driving the code
#=========================================================
def main()-> None:
    # ---- Ingestion process -----
    data = pd.read_csv('Data_files/hospital_encounters_raw.csv', skip_blank_lines=True,skiprows=3)
    key_columns = ['encounter_id','patient_id']
    
    # Landing Bronze
    df_valid, df_DLQ = dead_letter_queue(df=data, key_columns=key_columns)    

    # ---- Clean & Layout & Audit data process -----
    # -- Schema enforcement ----
    # 1. Cast all columns to a specific data type.
    cast_column_fix(df=df_valid, col='encounter_id', data_type=str)
    print(df_valid.head(5).to_string())

#===================================================================================================
    # ----- DQ checks -----
    # 1. ISO date format digest all input styles.
    # 2. Gender column has 3 values (m,f,o)
    # 3. Admition date <= release_date 
#===================================================================================================
    # df_iso = date_iso_all(df=df_valid)       
    # cols =  ["encounter_id","patient_id","gender","smoking_status", "admit_date", "admit_date_iso",
    #          "discharge_date", "discharge_date_iso", "length_of_stay_days", "encounter_type", "zip_code"
    #          , "phone"]
    # where = (pd.to_numeric(df_iso["length_of_stay_days"], errors="coerce") > 5)
    # print(df_iso.loc[where,cols].head(10).to_string()) 

    # cols =  ["encounter_id","patient_id","gender","smoking_status", "admit_date", "admit_date_iso",
    #          "discharge_date", "discharge_date_iso"]
    # df_tmp = df_iso.loc[(df_iso["admit_date_iso"]<=df_iso["discharge_date_iso"]),cols]

# -----------------------------------
if __name__ == "__main__":
    main()

# %%
data = pd.read_json