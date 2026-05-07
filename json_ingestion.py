#%% 
import pandas as pd
import json



def profiling(df:pd.DataFrame)->None:
    print('-'*50,'\n','--> INFO <--')
    print(df.info())
    print('-'*50,'\n','--> NULLS stat <--')
    print(df.isnull().sum())
    print('-'*50,'\n','--> DF sample <--')
    print(df.head(5).to_string())

# %%

def json_normelizer_fo_df(df:pd.DataFrame, data_col:str)->pd.DataFrame:
    try:

        with open("Data_files/patient_encounters_fhir.json",'r') as f:
            bundle = json.load(f)
        encountrers = bundle[data_col]
        json_normelized_df = pd.json_normalize(encountrers)
        return json_normelized_df        

    except Exception as e:
        raise Exception(f'--> Json_to_culoumn func FAILED, error msg: {e}')


def column_exploed(df:pd.DataFrame, col:str)->pd.DataFrame:
    try:

        df_col_explode = df[col].explode().add_prefix(f'{col}.')
        print(df_col_explode)
        df_json_normelized = pd.json_normalize(df_col_explode)
        print(df_json_normelized.head(5).to_string())

    except Exception as e:
        raise Exception(f'--> column_exploed func FAILED, error msg: {e}')

#-----------------------------------------------------

def main()->None:
    # ---- Ingestion -----
    json_data = pd.read_json('Data_files/patient_encounters_fhir.json') 
    df_json = json_normelizer_fo_df(df=json_data, data_col='entry')
    profiling(df=df_json)
  
    column_exploed(df_json, 'resource.name')
  # df_json_exp_gender = 

if __name__=='__main__':
    main()

# %%
