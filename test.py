#%% import modules
import pandas as pd
from functools import reduce
import json

#%% sum all values using reduce(lambda())
lst1 = [1,2,3,4,5,6,7,8,9,10]
dict1 = {'k1':1, 'k2': 2, 'k3' : 3, 'k4' : 4, 'k5' : 5}

res_1 = reduce(lambda x,y: x + y, lst1)
print(f'--> res1: {res_1}')

res_21 = reduce(lambda x,y: x+y, dict1.values())
print(f'--> res21: {res_21}')
res_22 = sum(dict1.values())
print(f'--> res22: {res_22}')

#%% sum all values using reduce(lambda()) filtering NaN/Nulls
lst2 = [1,2,3,4,None,6,7,None,9,10]
dict = {'k1':1, 'k2': None, 'k3' : 3, 'k4' : 4, 'k5' : 5, 'k6' : None}

flt_lst = list(filter(None,lst2))
print(flt_lst)
res_3 = reduce(lambda x,y: x+y , filter(None, lst2) )
print(f'--> res3: {res_3}')

flt_dict = list(filter(lambda kv: kv[1] is not None , dict.items()))
flt_dict = { k:v for k,v in dict.items() if v is not None }
print(flt_dict)

# %%


def extract_columns_from_nested_json(df:pd.DataFrame, col:str)->None:
    try:

        df_explode = df[col].explode()
        df_norm = pd.json_normalize(df_explode) # index is reset here
        df_norm.index = df_explode.index # restore the original index the the df for join validity
        df_extrat = df.merge(df_norm, left_index=True, right_index=True, how="left")
        df_extrat.drop(columns=[col],inplace=True)
        return df_extrat
    
    except Exception as e:
        raise Exception('--> DQ check 1 FAILD!!!')

with open ('Data_files/patient_encounters_fhir.json','r') as file:
    bundle = json.load(file)
    df = pd.json_normalize(bundle['entry'])

print(df.shape)
cols = ['resource.address','resource.identifier','resource.telecom','resource.reasonCode',
        'resource.extension','resource.participant','resource.name','telecom']
df_tmp = df

for col in cols:
    df_main = extract_columns_from_nested_json(df=df_tmp, col=col)
    df_tmp = df_main

print(df_tmp.head(10).to_string())
print(df_tmp.shape)



# %%
