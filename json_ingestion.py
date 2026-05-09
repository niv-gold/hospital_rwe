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

def ingest_json_to_df(df:pd.DataFrame, data_col:str)->pd.DataFrame:
    try:

        with open("Data_files/patient_encounters_fhir_10k.json",'r') as f:
            bundle = json.load(f)
        encountrers = bundle[data_col]
        json_normelized_df = pd.json_normalize(encountrers)
        return json_normelized_df        

    except Exception as e:
        raise Exception(f'--> ingest_json_to_df func FAILED, error msg: {e}')

def column_normalizing(df:pd.DataFrame, col:str)->pd.DataFrame:
    try:

        # Explode while preserving the source row index so we can rejoin safely.
        df_col_explode = df[col].explode()

        # Keep only dict-like payloads; scalars/nulls cannot be normalized reliably.
        mask_dict = df_col_explode.apply(lambda x: isinstance(x, dict))
        df_col_explode = df_col_explode[mask_dict]

        if df_col_explode.empty:
            return pd.DataFrame(index=df.index)

        df_json_normalized = pd.json_normalize(df_col_explode)
        df_json_normalized.index = df_col_explode.index

        # Collapse exploded rows back to one row per original index.
        # If multiple values exist for the same source row, keep a list.
        def _pack(values:pd.Series):
            vals = [v for v in values.tolist() if pd.notna(v)]
            if not vals:
                return np.nan
            if len(vals) == 1:
                return vals[0]
            return vals

        df_json_normalized = (
            df_json_normalized
            .groupby(level=0, sort=False)
            .agg(_pack)
            .reindex(df.index)
        )

        return df_json_normalized.add_prefix(f'{col}.')
    
    except Exception as e:
        raise Exception(f'--> column_exploed func FAILED, error msg: {e}')

def dict_column_normalizing(df:pd.DataFrame, col:str)->pd.DataFrame:
    try:

        df_col = df[col]
        mask_dict = df_col.apply(lambda x: isinstance(x, dict))
        df_col = df_col[mask_dict]

        if df_col.empty:
            return pd.DataFrame(index=df.index)

        df_json_normalized = pd.json_normalize(df_col)
        df_json_normalized.index = df_col.index
        df_json_normalized = df_json_normalized.reindex(df.index)

        return df_json_normalized.add_prefix(f'{col}.')

    except Exception as e:
        raise Exception(f'--> dict_column_normalizing func FAILED, error msg: {e}')

def has_nested_dict_payload(df:pd.DataFrame, col:str)->bool:
    try:

        series = df[col].dropna()
        if series.empty:
            return False

        if series.apply(lambda x: isinstance(x, dict)).any():
            return True

        return series.apply(
            lambda x: isinstance(x, list) and any(isinstance(i, dict) for i in x)
        ).any()

    except Exception as e:
        raise Exception(f'--> has_nested_dict_payload func FAILED, error msg: {e}')

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


def normalize_and_rejoin_columns(df:pd.DataFrame)->pd.DataFrame:
    try:

        columns_obj = [col for col in df.columns if has_nested_dict_payload(df, col)]
        for col in columns_obj:
            non_null_series = df[col].dropna()
            if non_null_series.empty:
                continue

            if non_null_series.apply(lambda x: isinstance(x, dict)).any():
                df_new_col = dict_column_normalizing(df, col)
            else:
                df_new_col = column_normalizing(df, col)

            if df_new_col.empty or df_new_col.shape[1] == 0:
                continue

            # join keeps row order/index stable and avoids merge expansion.
            df = df.join(df_new_col, how='left')
            df = df.drop(columns=[col])
        return df

    except Exception as e:
        raise Exception(f'--> explode_and_join_columns func FAILED, error msg: {e}')

def normalize_all_columns(df:pd.DataFrame, max_iterations:int=10)->pd.DataFrame:
    try:

        df_out = df.copy()
        for _ in range(max_iterations):
            cols_before = [col for col in df_out.columns if has_nested_dict_payload(df_out, col)]
            if not cols_before:
                break

            df_next = normalize_and_rejoin_columns(df_out)
            cols_after = [col for col in df_next.columns if has_nested_dict_payload(df_next, col)]

            df_out = df_next
            if cols_after == cols_before:
                break

        return normalize_residual_json_values(df_out)

    except Exception as e:
        raise Exception(f'--> normalize_all_columns func FAILED, error msg: {e}')

def normalize_residual_json_values(df:pd.DataFrame)->pd.DataFrame:
    try:

        df_out = df.copy()

        def _to_scalar_or_text(value):
            if isinstance(value, list):
                if len(value) == 0:
                    return np.nan
                if len(value) == 1 and not isinstance(value[0], (list, dict)):
                    return value[0]
                return json.dumps(value)
            if isinstance(value, dict):
                return json.dumps(value)
            return value

        for col in df_out.columns:
            if df_out[col].apply(lambda x: isinstance(x, (list, dict))).any():
                df_out[col] = df_out[col].apply(_to_scalar_or_text)

        return df_out

    except Exception as e:
        raise Exception(f'--> normalize_residual_json_values func FAILED, error msg: {e}')

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
        df_dlq = df[mask]
        df_valid = df[~mask]

        # append data:
        df_dlq["create_date"] = pd.Timestamp.now()
        df_dlq["update_date"] = pd.Timestamp.now()
        df_dlq["DQL_Status"] = "Faild"
        df_dlq["DQL_reason"] = "Failed Ingestion, key column is empty"
        df_dlq['reprocess']=False

        df_valid["create_date"] = pd.Timestamp.now()
        df_valid["update_date"] = pd.Timestamp.now()
        
        return df_valid, df_dlq

    except Exception as e:
        raise Exception(f'--> split_valid_dlq func FAILED, error msg: {e}')


def seperate_by_resourceType(df:pd.DataFrame, col_value:str)->pd.DataFrame:
    try:
        # print(df["resource.resourceType"].unique())
        df_patient = df[df["resource.resourceType"].str.strip().str.lower()==col_value.lower()].copy()
        return df_patient

    except Exception as e:
        raise Exception(f'--> FUNC seperate_patient_encounters_df FAILD, error msg: {e}')


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




#-----------------------------------------------------

def main()->None:
    # ---- sqllite engine ----/home/niv/GitRepos/hospital_rwe/Data_files/sqlite_db
    db_path = 'Data_files/sqlite_db'
    eng_bronze = create_engine(f'sqlite:///{db_path}/bronze.db')
    eng_silver = create_engine(f'sqlite:///{db_path}/silver.db')
    eng_gold = create_engine(f'sqlite:///{db_path}/gold.db')

    # ---- Ingestion -----
    json_data = pd.read_json('Data_files/patient_encounters_fhir.json') 
    df_json = ingest_json_to_df(df=json_data, data_col='entry')   
    df_main = normalize_all_columns(df=df_json)
    df_patient = seperate_by_resourceType(df=df_main,col_value='Patient')
    df_encounter = seperate_by_resourceType(df=df_main,col_value='Encounter')
    key_cols_lst = ['resource.id']
    df_patient_valid, df_patient_dlq = split_valid_dlq(df=df_patient,key_cols=key_cols_lst)
    df_patient_valid.to_sql(name='patients', con=eng_bronze, index=False, if_exists="replace")
    # print(df_patient_valid.head(5).to_string())
    # print(df_patient_dlq.head(5).to_string())
    df_encounter_valid, df_encounter_dlq = split_valid_dlq(df=df_encounter,key_cols=key_cols_lst)
    df_encounter_valid.to_sql(name='encounters', con=eng_bronze, index=False, if_exists="replace")
    # print(ddf_encounter_valid.head(5).to_string())
    # print(df_encounter_dlq.head(5).to_string())
    df_patient_dlq.to_sql(name='patient_dlq', con=eng_bronze, index=False, if_exists="append")
    df_encounter_dlq.to_sql(name='encounter_dlq', con=eng_bronze, index=False, if_exists="append")


    # ---- cleaning data ----
    df_raw_encounter = pd.read_sql('SELECT * FROM encounters', con=eng_bronze)
    df_enc_w_s_clean = clean_whit_spaces(df=df_raw_encounter)
    df_enc_lowercase = lowe_casing_str_cols(df_enc_w_s_clean)    
    df_enc_lowercase.to_sql(name='encounters_cln', con=eng_silver, index=False, if_exists="replace")
    # print(df_enc_lowercase.head(5).to_string())

    df_raw_patient = pd.read_sql('SELECT * FROM patients', con=eng_bronze)
    df_pat_w_s_clean = clean_whit_spaces(df=df_raw_patient)
    df_pat_lowercase = lowe_casing_str_cols(df_pat_w_s_clean)    
    df_pat_lowercase.to_sql(name='patient_cln', con=eng_silver, index=False, if_exists="replace")
    # print(df_pat_lowercase.head(5).to_string())

    # ---- filtering valid rows ----
    df_encounter_cln = pd.read_sql_table('encounters_cln', con=eng_silver)
    key_cols_lst = ['resource.id']
    df_enc_valid,df_enc_dlq = split_valid_dlq(df=df_encounter_cln,key_cols=key_cols_lst)
    df_enc_valid.to_sql(name='encounter', con=eng_gold, index=False, if_exists="replace")
    df_enc_dlq.to_sql(name='encounter_dlq', con=eng_bronze, index=False, if_exists="replace")
    
    print('--> VALID ENCOUNTER DF <--\n',df_enc_valid.head(5).to_string())
    print('--> ENCOUNTER DLQ DF <--\n',df_enc_dlq.head(5).to_string())

    df_pat_cln = pd.read_sql_table('patient_cln', con=eng_silver)
    key_cols_lst = ['resource.id']
    df_pat_valid,df_pat_dlq = split_valid_dlq(df=df_pat_cln,key_cols=key_cols_lst)
    df_pat_valid.to_sql(name='patient', con=eng_gold, index=False, if_exists="replace")
    df_pat_dlq.to_sql(name='patient_dlq', con=eng_bronze, index=False, if_exists="replace")

    print('--> VALID PATIENT DF <--\n',df_pat_valid.head(5).to_string())
    print('--> PATIENT DLQ DF <--\n',df_pat_dlq.head(5).to_string())

    #-- DQ check:
    # df_iso = date_iso_all(df=df_encounter_cln)
    # print(df_iso.to_string())

    
if __name__=='__main__':
    main()

# %%
