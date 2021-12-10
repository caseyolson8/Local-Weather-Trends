import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
# from pprint import pprint
import helper as hp

####   Pipeline to process imported data   ####
# test line again
data_path ='~/Desktop/capstone/data/Denver_1940_2010.csv'
raw_data_df = pd.read_csv(data_path, low_memory=False)

dates_r = hp.grab_datetime(raw_data_df)
PRCP_r = hp.grab_col_data(raw_data_df, 'PRCP')
TMAX_r = hp.grab_col_data(raw_data_df, 'TMAX')
TMIN_r = hp.grab_col_data(raw_data_df, 'TMIN')

PRCP_d = hp.GHCN_Data(PRCP_r, dates_r, *hp.trim_col_data(PRCP_r))
TMAX_d = hp.GHCN_Data(TMAX_r, dates_r, *hp.trim_col_data(TMAX_r))
TMIN_d = hp.GHCN_Data(TMIN_r, dates_r, *hp.trim_col_data(TMIN_r))

TMAX_d.set_data_by_year()

TMAX_d.time_yr

print(TMAX_d.data_yr[1,0:20])


'''
good = ~data['PRCP'].isna()

X = data['DATE'][good].to_numpy()
Y = data['PRCP'][good].to_numpy()


fig, ax = plt.subplots(1)
ax.plot(X, Y)
plt.show()
'''