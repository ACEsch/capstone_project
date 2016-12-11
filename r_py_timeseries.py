# Wrapper on R dataframe Integration with python

# all necessary Python library

import numpy as np
import scipy as sp
import pandas as pd
import rpy2
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
import rpy2.robjects as ro
import pandas.rpy.common as com
import warnings
warnings.filterwarnings("ignore")
warnings.simplefilter(action = "ignore", category = FutureWarning)

# all necessary R libraries

stats = importr('stats')
base = importr('base')
datasets = importr('datasets')
graph = importr('graphics')
forecast = importr('forecast')
fortify = importr('ggfortify')
vars = importr('vars')
zoo = importr('zoo')

ro.r('library(forecast)')

class ts_generic():

    def __init__(self):
        pass

    @staticmethod
    def py_to_r(df, r_df_name):
        """
        :param df:  pandas data frame
        :param name:  saved r data frame in R environment
        :return:
        """
        r_df = pandas2ri.py2ri(df)
        ro.globalenv[r_df_name] = r_df
        return None

    @staticmethod
    def r_to_py(r_df_name):
        """
        :param r_df_name: the r data frame NAME saved in R environment
        :return:
        """
        ro.globalenv['\'' + str(r_df_name) + '\''] = r_df_name
        return com.load_data('\'' + str(r_df_name) + '\'')

    @staticmethod
    def r_to_ts(r_df_name, r_ts_name, freq=365):
        """
        :param r_df_name:  convert python data frame to r ts
        :return:
        """
        r_ts = stats.ts(r_df_name, start=1, frequency=freq)
        ro.globalenv[r_ts_name] = r_ts
        return None

    @staticmethod
    def py_to_ts(df, r_ts_name, freq=365):
        """
        :param r_df_name:  convert a R data frame to r ts - dirct
        :return:
        """
        r_df_name = pandas2ri.py2ri(df)
        r_ts = stats.ts(r_df_name, start=1, frequency=freq)
        ro.globalenv[r_ts_name] = r_ts
        return None

    @staticmethod
    def py_to_ts_zoo(df, r_ts_name, freq=365):
        """
        default to be a daily index  - o/w needs to change the format parameters
        :param r_df_name:  convert a R data frame to r ts
        :return:

        """
        r_df_name = pandas2ri.py2ri(df)
        ro.globalenv['tmp_ts'] = r_df_name
        r_ts = ro.r('zoo(tmp_ts)')
        ro.globalenv[r_ts_name] = stats.ts(r_ts)
        # base.rm('tmp_ts')
        return None

class arima(ts_generic):

    def __init__(self, df, pred_step=1):
        self.data = df
        self.step = pred_step
        self.result = None

    def arima_predict_next(self, sub_df):
        """
        :param sub_df: here sub_df is one column dataframe
        :return:
        """
        base.rm('tmp')
        print sub_df
        self.py_to_r(sub_df, 'tmp')
        print type(ro.globalenv['tmp'])
        func_param = "as.data.frame(forecast(auto.arima(tmp),h=step))".replace("step", str(self.step))
        # pred_step = ro.r('\'' + str(func_param) + '\'')
        pred_step = ro.r(func_param)
        # print self.r_to_py(pred_step)
        return self.r_to_py(pred_step)
        base.rm('\'' + str(pred_step) + '\'') #clean the memory


    def arima_predict_df(self, in_sample_count = 450):
        """
        # method to wrap the udpdate on the dataframe level
        :param master_df:
        :param in_sample_count:
        :return:
        """
        df_init = pd.DataFrame(index=self.data.index, columns=self.data.columns)
        df_init.iloc[:in_sample_count, :] = self.data.iloc[:in_sample_count, :]

        for col in df_init.columns:
            for row in df_init.iloc[in_sample_count:,:].index:
                # update each entries by entries by calling single predict function
                print (row, col)
                tmp_df = df_init[[col]].dropna()
                tmp_df[[col]] = tmp_df[[col]].astype(float)
                print tmp_df
                # tmp_df.astype(float)
                # print tmp_df.shape
                tmp_res = self.arima_predict_next(tmp_df[col])
                print tmp_res.iloc[0]['Point Forecast']
                df_init.loc[row,[col]] = tmp_res.iloc[0]['Point Forecast']
                del tmp_df

        self.result = df_init

    def __call__(self, *args, **kwargs):
        return self.arima_predict_df()


class holt_winter(ts_generic):

    def __init__(self, df, pred_step=1):
        self.data = df
        self.step = pred_step
        self.result = None

    def hw_predict_next(self, sub_df):
        """
        :param sub_df: here sub_df is one column dataframe
        :return:
        """
        base.rm('tmp')
        print sub_df
        self.py_to_ts(sub_df, 'tmp')
        print type(ro.globalenv['tmp'])
        print ro.globalenv['tmp']
        func_param = "as.data.frame(forecast(HoltWinters(tmp,gamma = FALSE),h=step))".replace("step", str(self.step))
        print func_param
        pred_step = ro.r(func_param)
        print pred_step
        return self.r_to_py(pred_step)
        base.rm('\'' + str(pred_step) + '\'') #clean the memory

    def hw_predict_df(self, in_sample_count=450):
        """
        # method to wrap the udpdate on the dataframe level
        :param master_df:
        :param in_sample_count:
        :return:
        """
        df_init = pd.DataFrame(index=self.data.index, columns=self.data.columns)
        df_init.iloc[:in_sample_count, :] = self.data.iloc[:in_sample_count, :]

        for col in df_init.columns:
            for row in df_init.iloc[in_sample_count:, :].index:
                # update each entries by entries by calling single predict function
                print (row, col)
                tmp_df = df_init[[col]].dropna()
                tmp_df[[col]] = tmp_df[[col]].astype(float)
                print tmp_df
                # tmp_df.astype(float)
                # print tmp_df.shape
                tmp_res = self.hw_predict_next(tmp_df[col])
                print tmp_res.iloc[0]['Point Forecast']
                df_init.loc[row, [col]] = tmp_res.iloc[0]['Point Forecast']
                del tmp_df

        self.result = df_init

    def __call__(self, *args, **kwargs):
        return self.hw_predict_df()


if __name__ == "__main__":

    ### test arima data frame version ###
    # np.random.seed(0)
    # count = np.random.rand(457,2)
    # df = pd.DataFrame(index=pd.date_range('2016-01-01', '2017-04-01'), data=count, columns=['count1','count2'])
    # print df.shape
    # print df.head(5)
    # arima_test = arima(df)
    # arima_test()
    # print arima_test.result

    ### test arima ###
    # count = np.random.rand(214, 1)
    # df = pd.DataFrame(index=pd.date_range('2016-01-01', '2016-08-01'), data=count, columns=['count1'])
    # arima_test = arima(df)
    # arima_test.arima_predict_next(df['count1'])

    ### test HW ###
    count = np.random.rand(214, 1)
    df = pd.DataFrame(index=pd.date_range('2016-01-01', '2016-08-01'), data=count, columns=['count1'])
    Hw_test = holt_winter(df)
    Hw_test.hw_predict_next(df['count1'])

    ### test arima data frame version ###
    # np.random.seed(0)
    # count = np.random.rand(457,2)
    # df = pd.DataFrame(index=pd.date_range('2016-01-01', '2017-04-01'), data=count, columns=['count1','count2'])
    # print df.shape
    # print df.head(5)
    # hw_test = holt_winter(df)
    # hw_test()
    # print hw_test.result

    ### test var ###
    # count = np.random.rand(214, 3)
    # df = pd.DataFrame(index=pd.date_range('2016-01-01', '2016-08-01'), data=count, columns=['count1','count2','count3'])
    # print df
    # var_test = var(df)
    # var_test.var_predict_next(df)

