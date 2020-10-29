import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.regression import linear_model
import scipy.stats as stats


########   DATA STORAGE CLASSES   ########
month_lst = []
for dy in range(0,366):
    month_lst.append((datetime(2020,1,1)+timedelta(days=dy)).month)
month_lut = {1: 'Jan.',
             2: 'Feb.',
             3: 'Mar.',
             4: 'Apr',
             5: 'May',
             6: 'June',
             7: 'July',
             8: 'Aug.',
             9: 'Sept.',
             10: 'Oct.',
             11: 'Nov.',
             12: 'Dec.'}

ylabel_dict = { 'PRCP_sum' : 'Precipitation (inches)',
                'TMAX_avg' : r'Average Highs ($^\circ$F)',
                'TMIN_avg' : r'Average Lows ($^\circ$F)',
                'SNOW_sum' : 'Total Snowfall (inches)',
                'SNWD_cnt' : '# Days with Snow Cover (n days)'}
               



class GHCN_Loc():
    def __init__(self, pathway, filterbyloc = ''):
        if filterbyloc:
            temp = pd.read_csv(pathway, low_memory=False)
            self.raw_df = temp[temp['NAME']==filterbyloc].reset_index()
        else:
            self.raw_df = pd.read_csv(pathway, low_memory=False)
            
        self.dates = grab_datetime(self.raw_df)
        self.location = self.raw_df['NAME'][0]
        if 'LATITUDE' in self.raw_df:
            self.latitude = self.raw_df['LATITUDE'][0]
            self.longitude = self.raw_df['LONGITUDE'][0]
        else:    # Default to Denver #
            self.latitude = 39.76746
            self.longitude = -104.86948
        self.start, self.end = trim_col_data(self.raw_df['TMAX'])
        self.day_start = 0
        self.day_stop = 366
        
    def set_range(self, start, end):
        # arguments start and end are datetime objects with Year, Month, Day
        # if method '.process' is run after this it will filter data in this range
        if start in self.dates:
            self.start = self.dates.index(start)
        else:
            self.start = self.dates.index(min(self.dates))
        
        self.end = self.dates.index(end)+1
    
    def process(self):
        self.PRCP = self.create_data_object('PRCP')
        self.TMAX = self.create_data_object('TMAX')
        self.TMIN = self.create_data_object('TMIN')
        self.SNOW = self.create_data_object('SNOW')
        self.SNWD = self.create_data_object('SNWD')
    
    def create_aggregate_df(self):
        # Note: pd.df. sum() & mean() ignore nan values
        yearly_prcp = pd.Series(self.PRCP.data_yr.iloc[:,1:].sum().values, name = 'PRCP_sum')
        yearly_tmax = pd.Series(self.TMAX.data_yr.iloc[:,1:].mean().values, name = 'TMAX_avg')
        yearly_tmin = pd.Series(self.TMIN.data_yr.iloc[:,1:].mean().values, name = 'TMIN_avg')
        yearly_snow = pd.Series(self.SNOW.data_yr.iloc[:,1:].sum().values, name = 'SNOW_sum')
        yearly_snwd = pd.Series((self.SNWD.data_yr.iloc[:,1:]>0.0).sum().values, name = 'SNWD_cnt')
        self.agg_df = pd.DataFrame({'Year' : self.PRCP.data_yr.columns[1:],
                                    'PRCP_sum' : yearly_prcp,
                                    'TMAX_avg' : yearly_tmax,
                                    'TMIN_avg' : yearly_tmin,
                                    'SNOW_sum' : yearly_snow,
                                    'SNWD_cnt' : yearly_snwd})
        
    def create_sampled_df(self):
        rows = range(self.day_start,self.day_stop)
        sample_prcp = pd.Series(self.PRCP.data_yr.iloc[rows,1:].sum().values, name = 'PRCP_sum')
        sample_tmax = pd.Series(self.TMAX.data_yr.iloc[rows,1:].mean().values, name = 'TMAX_avg')
        sample_tmin = pd.Series(self.TMIN.data_yr.iloc[rows,1:].mean().values, name = 'TMIN_avg')
        sample_snow = pd.Series(self.SNOW.data_yr.iloc[rows,1:].sum().values, name = 'SNOW_sum')
        sample_snwd = pd.Series((self.SNWD.data_yr.iloc[rows,1:]>0.0).sum().values, name = 'SNWD_cnt')
        self.sampled_df = pd.DataFrame({'Year' : self.PRCP.data_yr.columns[1:],
                                    'PRCP_sum' : sample_prcp,
                                    'TMAX_avg' : sample_tmax,
                                    'TMIN_avg' : sample_tmin,
                                    'SNOW_sum' : sample_snow,
                                    'SNWD_cnt' : sample_snwd})
        
        
        
        
        
        
    def stats(self, ax, agg_name, alpha=0.05, to_plot=True, sampled=False):


        if sampled:
            Y = self.sampled_df[agg_name].values
            n = len(Y)
            X = np.ones((n, 2))
            X[:,0] = self.sampled_df['Year'].values        
        else:
            Y = self.agg_df[agg_name].values
            n = len(Y)
            X = np.ones((n, 2))
            X[:,0] = self.agg_df['Year'].values        
            

        model = linear_model.OLS(Y,X)
        results = model.fit()
        params = results.params
        CI = results.conf_int(alpha=alpha, cols=None)[0]
        
        X_mdl = X[:,0]
        Y_mdl = X_mdl*params[0] + params[1]
        
        if to_plot:
            ax.scatter(X[:,0], Y, c='b')


    #         CI_L = {:.4f}.format(CI[0]).rstrip('0')
    #         CI_H = {:.4f}.format(CI[1]).rstrip('0')
            a = '{:.4f}'.format(alpha).rstrip('0')

            mdl_label = 'Simple Linear Regression'
    #         mdl_label = '''Fit Line, slope CI:[{:.4f},{:.4f}] 
    #                     @ p = '''.format(CI[0], CI[1]) + a
            ax.plot(X_mdl, Y_mdl, 'r', label=mdl_label)
            ax.set_xlabel('Years', fontsize = 25)
            ax.set_ylabel(ylabel_dict[agg_name], fontsize = 20)

            ## Calculate the Confidence Interval bounds
            ## 95% confidence that the mean of the dist. is within these bounds
            sigma = np.sqrt(((Y_mdl - Y)**2).sum()/(n-2))
            t_stat = stats.t.ppf(1-alpha/2, n - 2)     # For two-tailed test
            den = sum((X[:,0]-X[:,0].mean())**2)
            interval = (X[:,0]-X[:,0].mean())/den
            CI_interval = t_stat*sigma*np.sqrt((1/n) + interval)
            CI_up_bound = Y_mdl + CI_interval
            CI_low_bound = Y_mdl - CI_interval
            ax.fill_between(X_mdl, CI_up_bound, CI_low_bound, facecolor=[1, 0, 0, 0.15], label='{:.2f} Confidence Bounds'.format(1-alpha))
    #         ax.plot(X_mdl, CI_up_bound, 'r--', label='CI bounds')
    #         ax.plot(X_mdl, CI_low_bound, 'r--')

            ## Calculate the Prediction Interval bounds
            ## 95% confidence that the mean of the dist. is within these bounds
            PR_interval = t_stat*sigma*np.sqrt(1 + (1/n) + interval)
            PR_up_bound = Y_mdl + PR_interval
            PR_low_bound = Y_mdl - PR_interval
    #         ax.plot(X_mdl, PR_up_bound, 'r.', label='Pred. bounds')
    #         ax.plot(X_mdl, PR_low_bound, 'r.')
            ax.fill_between(X_mdl, PR_up_bound, PR_low_bound, color=[1, 0, 0, 0.1], label='{:.2f} Prediction Bounds'.format(1-alpha))
        
        return CI

    
    def create_data_object(self, col_name):
        col_data = grab_col_data(self.raw_df, col_name)
        self.start
        data = GHCN_Data(col_data, self.dates, self.start, self.end)
        #data = GHCN_Data(col_data, self.dates, *trim_col_data(col_data))
        data.set_data_by_year()
        return data
    




class GHCN_Data():
    # Data class to help parse weather data from the GHCN data set
    def __init__(self, data, times, start=0, stop=np.nan):
        if len(data) != len(times):
            print("data & times aren't the same size")
        
        self.data = np.array(data)
        self.time = np.array(times)
        
        self.start = start
        if np.isnan(stop):
            self.stop = len(data)
        else:
            self.stop = stop
        
    def set_start(self, start):
        self.start = start
    
    def set_stop(self, stop):
        self.stop = stop
        
    def clean_data(self):
        # Returns the cleaned data
        return self.data[self.start:self.stop]
    
    def clean_times(self):
        return self.time[self.start:self.stop]
    
    def set_yrs(self):
        data_years    =   set([dt.year for dt in self.clean_times()])
        self.startyr  =   min(data_years)
        self.endyr    =   max(data_years)
    # def clean_by_year(self):
    #     return self.time[self.start:self.stop]
    
    def set_data_by_year(self):
        self.set_yrs()
        yr_range = self.endyr - self.startyr
        data_yr = np.ones((366,yr_range+1), dtype=float)*np.nan

        for dt, data in zip(self.clean_times(), self.clean_data()):
            col = dt.year - self.startyr
            if dt.month <= 2:
                row = (dt - datetime(dt.year, 1, 1)).days
            else:
                row = (dt - datetime(dt.year, 3, 1)).days + 60
            data_yr[row, col] = data
        df = pd.DataFrame(data_yr)
        df.columns = np.arange(self.startyr, self.endyr+1)
        df.insert(loc=0, column='Month_id', value=month_lst)
        self.data_yr = df
        

        
    
########   Data Parsing Functions   ########
    
def grab_col_data(df, col_name):
    """
    Returns a data of 'col_name' from dataframe 'df'
    as a np.array() object
    """
    return np.array([x for x in df[col_name]])
    
def grab_datetime(df):
    """
    Returns the 'DATE' column of dataframe 'df'
    as a np.array() object of datetime objects
    """
    lst = []
    dt_split = [datetime(*tuple([int(y) for y in x.split('-')])) for x in df['DATE']]
    return dt_split

def trim_col_data(col_data, start=np.nan, stop=np.nan):
    """
    In: 1 dim. array, (optional) stop & start indices
    Operation:  If indices aren't passed then it finds the start as first non-nan data
    & stop as the final non-nan data
    Return:  Also the stop & start as a tuple.
            not the Col_data array by the start & stop indices.
    """
    if np.isnan(start):
        non_ids = np.where(~np.isnan(col_data)==True)[0]
        start = non_ids[0]
        if np.isnan(stop):
            stop = non_ids[-1]
    elif np.isnan(stop):
        non_ids = np.where(~np.isnan(col_data)==True)[0]
        stop = non_ids[-1]
    
    return start, stop



########   DATA Viz Functions   ########

def signal_avg(Y, time_avg):
    Y_avg = []
    for idx in range(0,len(Y)-time_avg):
        Y_avg.append(Y[idx:idx+time_avg].mean())
    return Y_avg

def plot_year(ax, df, year, time_avg=1):
    Y_val = df[year].values
    if time_avg > 1:
        Y = signal_avg(Y_val, time_avg)
        
    ax.plot(Y, label=str(year))
    
def plot_month(ax, df, year, month, time_avg=1):
    Y_val = df[df['Month_id']==month][year].values
    if time_avg > 1:
        Y = signal_avg(Y_val, time_avg)
    ax.plot(Y, label=str(year))
    
##  REF: http://www.variousconsequences.com/2010/02/visualizing-confidence-intervals.html
##  http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/CurveFitting.ipynb

# def plot_ci_bands(model, alpha= 0.05):