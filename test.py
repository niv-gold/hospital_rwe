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
