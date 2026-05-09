#%% 
import pandas as pd
import numpy as np
import json
from functools import reduce
from sqlalchemy import create_engine



def profiling(df:pd.DataFrame)->None:
    print('-'*50,'\n','--> INFO <--')
    print(df.info())
    print('-'*50,'\n','--> NULLS stat <--')
    print(df.isnull().sum())
    print('-'*50,'\n','--> DF sample <--')
    print(df.head(20).to_string())

def json_normelizer_fo_df(df:pd.DataFrame, data_col:str)->pd.DataFrame:
    try:

        with open("Data_files/patient_encounters_fhir_10k.json",'r') as f:
            bundle = json.load(f)
        encountrers = bundle[data_col]
        json_normelized_df = pd.json_normalize(encountrers)
        return json_normelized_df        

    except Exception as e:
        raise Exception(f'--> Json_to_culoumn func FAILED, error msg: {e}')

def column_exploed(df:pd.DataFrame, col:str)->pd.DataFrame:
    try:

        df_col_explode = df[col].explode()  
        df_json_normelized = pd.json_normalize(df_col_explode).add_prefix(f'{col}.')
        return df_json_normelized
    
    except Exception as e:
        raise Exception(f'--> column_exploed func FAILED, error msg: {e}')

def get_df_columns_by_type(df:pd.DataFrame, col_type:type, method)->list:
    try:

        df_columns = [col for col in df.columns]
        lst_cols_arry = []
        for col in df_columns:
            non_null_series = df[col].dropna()
            # Avoid vacuous truth: all([]) returns True for fully-null columns.
            if non_null_series.empty:
                continue
            if method(non_null_series.apply(lambda x: isinstance(x, col_type))):
                lst_cols_arry.append(col)

        return lst_cols_arry

    except Exception as e:
        raise Exception(f'--> get_df_columns_by_type func FAILED, error msg: {e}')

def explode_and_join_columns(df:pd.DataFrame)->pd.DataFrame:
    try:

        # df_json_exp_gender = column_exploed(df_json, 'resource.name')
        columns_obj = get_df_columns_by_type(df=df, col_type=list, method=any)
        for col in columns_obj:
            df_new_col = column_exploed(df, col).dropna()            
            df = df.merge(df_new_col, left_index=True, right_index=True, how='left')
        return df

    except Exception as e:
        raise Exception(f'--> explode_and_join_columns func FAILED, error msg: {e}')

def clean_whit_spaces(df:pd.DataFrame)->pd.DataFrame:
    'using apply to lower case as a data series'
    try:

        col_str_lst = get_df_columns_by_type(df=df, col_type=str, method=any)
        for col in col_str_lst:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        return df


    except Exception as e:
        raise Exception(f'--> clean_whit_spaces func FAILED, error msg: {e}')
    

def lowe_casing_str_cols(df:pd.DataFrame)->pd.DataFrame:
    'using lower case as a vector'
    try:

        col_str_lst = get_df_columns_by_type(df=df, col_type=str, method=any)
        for col in col_str_lst:
            df[col] = df[col].apply(lambda x: x.lower() if isinstance(x, str) else x)
        return df
    
    except Exception as e:
        raise Exception(f'--> lowe_casing_str_cols func FAILED, error msg: {e}')

def split_valid_dlq(df:pd.DataFrame, key_cols:list[str])->tuple[pd.DataFrame,pd.DataFrame]:
    try:

        cond = [df[k_col].isnull() for k_col in key_cols]
        mask = reduce(lambda x,y: x|y , cond)
        df_dlq = df[mask].copy()
        df_valid = df[~mask].copy()
        df_dlq['dlq_reprocess']=False
        
        return df_valid, df_dlq

    except Exception as e:
        raise Exception(f'--> split_valid_dlq func FAILED, error msg: {e}')

def serialize_lists(df):
    try:
        for col in df.columns:
            # Find columns that contain lists or dicts
            if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
                )
        return df
    except Exception as e:
        raise Exception(f'--> FUNC "serialize_lists" FAILD, error msg: {e}')
    

def date_iso_all(df:pd.DataFrame)->pd.DataFrame:
    try:
        
        lst_col_dt = [col for col in df.columns 
                                if any(sub in col.lower() for sub in ['date','period'])
                            ]
        for col in lst_col_dt:
            df_iso_col = date_iso(df=df,col=col)
        return df_iso_col

    except Exception as e:
        raise Exception(f'--> FUNC date_iso_all FAILED, error msg: {e}')

def date_iso(df:pd.DataFrame, col:str)->pd.DataFrame:
    'alinging all data format into the universal YYYY-MM-DD'
    try:
        
        
        col_dt_iso = f'{col}_iso'
        df[col_dt_iso] = pd.to_datetime(df[col], errors='coerce', format=None)
        df_iso = is_date_iso_embigues(df=df, col=col_dt_iso)
        return df_iso

    except Exception as e:
        raise Exception(f'--> FUNC normalize_dates FAILED, error msg: {e}')
    

def is_date_iso_embigues(df:pd.DataFrame, col:str)->pd.DataFrame:
    try:
        
        df[f'{col}_is_mbg'] = np.where((df[col].dt.day <= 12) & (df[col].dt.month <= 12),1,0)
        return(df)
    
    except Exception as e:
        raise Exception(f'--> FUNC is_date_iso_embigues FAILED, error msg: {e}')


def dq_date_end_befor_start(df:pd.DataFrame)->None:
    try:
        pass
    except Exception as e:
        raise Exception('--> DQ check 1 FAILD!!!')

def dq_null_key_columns_(df:pd.DataFrame)->None:
    try:
        pass
    except Exception as e:
        raise Exception('--> DQ check 2 FAILD!!!')
    
def dq_value_string_NaN(df:pd.DataFrame)->None:
    try:
        pass
    except Exception as e:
        raise Exception('--> DQ check 3 FAILD!!!')
    

#-----------------------------------------------------

def main()->None:
    # ---- sqllite engine ----/home/niv/GitRepos/hospital_rwe/Data_files/sqlite_db
    db_path = 'Data_files/sqlite_db'
    eng_bronze = create_engine(f'sqlite:///{db_path}/bronze.db')
    eng_silver = create_engine(f'sqlite:///{db_path}/silver.db')
    eng_gold = create_engine(f'sqlite:///{db_path}/gold.db')

    # ---- Ingestion -----
    json_data = pd.read_json('Data_files/patient_encounters_fhir.json') 
    df_json = json_normelizer_fo_df(df=json_data, data_col='entry')     
    df_main = explode_and_join_columns(df=df_json)
    df_deserilized = serialize_lists(df_main)
    df_deserilized.to_sql(name='encounters', con=eng_bronze, index=False, if_exists="replace")

    # ---- cleaning data ----
    df_raw_encounter = pd.read_sql('SELECT * FROM encounters', con=eng_bronze)
    df_w_s_clean = clean_whit_spaces(df=df_raw_encounter)
    df_lowercase = lowe_casing_str_cols(df_w_s_clean)    
    df_lowercase.to_sql(name='encounters_cln', con=eng_silver, index=False, if_exists="replace")

    # ---- filtering valid rows ----
    df_encounter_cln = pd.read_sql_table('encounters_cln', con=eng_silver)
    key_cols_lst = ['resource.id','resource.identifier']
    df_valid,df_dlq = split_valid_dlq(df=df_encounter_cln,key_cols=key_cols_lst)
    df_valid.to_sql(name='encounters', con=eng_gold, index=False, if_exists="replace")
    df_dlq.to_sql(name='encounter_dlq', con=eng_bronze, index=False, if_exists="replace")
    
    print('--> VALID DF <--\n',df_valid.to_string())
    # print('--> DLQ DF <--\n',df_dlq.head(5).to_string())

    #-- DQ check:
    # df_iso = date_iso_all(df=df_encounter_cln)
    # print(df_iso.to_string())

    
if __name__=='__main__':
    main()

# %%
