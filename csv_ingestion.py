
#%%
import pandas as pd
import functools
from functools import reduce
import logging

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

    print('== fd column stat ==')
    columns = [col for col in df.columns]
    for col in columns:
        print(f'Colomn - {col}')        
        print(f'Null count: {df[col].isnull().sum()}')
        print(f'duplicate rows in column: {df[col].duplicated().sum()}')
        print(f'Data sample: {df[col].unique()[:5]}')

        print('-'*50)

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


# @pipe_error_handler
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
def gender_format_fix(df:pd.DataFrame)-> pd.DataFrame:
    # TBD: unified all genders under a unified output: M=male, F=Female, O=Other(include Null)
    lst_gnd = df["gender"].unique()
    # print(lst_gnd)
    lst_col_str = df.query("gender in ['1','2']")[['patient_name','gender']]

@pipe_error_handler
def date_format_fix(df:pd.DataFrame)->pd.DataFrame:
    # TBD: fix a data column with mix date formats, output a universal format YYYY-MM-DD
    pass


@pipe_error_handler
def phone_format_fix(df:pd.DataFrame)-> pd.DataFrame:
    # TBD: unifide all phone number into one format [+\n\n\n-\n\n-\n\n\n-\n\n\n\n]
    pass

def smokin_format_fix(df:pd.DataFrame)-> pd.DataFrame:
    # TBD: unified smoking status uder a close list of defined values: F=former, N=ever, C=Current, U=Unknown .
    pass

@pipe_error_handler
def phi_cols_registry(tbl:str, col:str, classification:str='phi', encrypt:bool=1, method:str='mask')-> None:
    # TBD: regestry PII/PHI columns to be masked or tokenized befor gold layer 
    # pd.DataFrame([
    # {"table": "silver_patients", "column": "ssn", "classification": "PHI", "encryption_required": True}, "method": ["mask" or "tokenize"]])
    pass


# TBD:
# 1. create serugate keys for columns that holde a list of string: Gender, insurance, smoling
# 2. check what do we do with missing Key values: Encounter_id, patient_id, (CPT), (ICD-10/9)
# 3. find out the meaning of Nan on the following fildes: CPT and ICD-10 (dose NaN will rerout to DLQ)


#=========================================================
# Running Block - driving the code
#=========================================================
def main()-> None:
    data = pd.read_csv('Data_files/hospital_encounters_raw.csv', skip_blank_lines=True,skiprows=3)
    # profiling(df=data, df_name='Patient_Encounters')
    
    key_columns = ['encounter_id','patient_id']
    df_valid, df_DLQ = dead_letter_queue(df=data, key_columns=key_columns)

    print(df_DLQ.shape)
    print(df_DLQ.head(100).to_string())

    # df_clean = df_column_strip(df=df_valid)  
    # profiling(df=df_clean, df_name='Patient_Encounters') 
    

# -----------------------------------
if __name__ == "__main__":
    main()

# %%
