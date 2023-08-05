import matplotlib.pyplot as plt
import predict_util
import getWeekday
import load_weather
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LinearRegression
import warnings

    
def forecast_multifeather(bld_name, load_weekday, n_train, n_lag, Temp_weekday, Huminity_weekday, WindSpeed_weekday, Day_period):
    n_days = int(load_weekday.size / T)

    MAPE_sum_nn = 0.0
    RMSPE_sum_nn = 0.0
    MAPE_sum_rf = 0.0
    RMSPE_sum_rf = 0.0
    MAPE_sum_lr = 0.0
    RMSPE_sum_lr = 0.0

    # 5 set of features
    # (1) load
    # (2) temperature
    # (3) huminity
    # (4) windspeed
    # (5) day period

    for curr_day in range(n_train + n_lag, n_days-1):
        # build training data
        y_train = np.zeros((n_train, T))
        X_train = np.zeros((n_train, 5 * T * n_lag))
        for row, train_day in enumerate(range(curr_day - n_train, curr_day)):
            y_train[row,:] = load_weekday[train_day * T : train_day * T + T]
            X_train[row,0*T*n_lag:1*T*n_lag] = load_weekday[train_day * T - n_lag * T: train_day * T]
            X_train[row,1*T*n_lag:2*T*n_lag] = Temp_weekday[train_day * T - n_lag * T: train_day * T]
            X_train[row,2*T*n_lag:3*T*n_lag] = Huminity_weekday[train_day * T - n_lag * T: train_day * T]
            X_train[row,3*T*n_lag:4*T*n_lag] = WindSpeed_weekday[train_day * T - n_lag * T: train_day * T]
            X_train[row,4*T*n_lag:5*T*n_lag] = Day_period[train_day * T - n_lag * T: train_day * T]
        # building test data
        X_test = np.zeros((1, 5 * T * n_lag))
        X_test[0, 0*T*n_lag:1*T*n_lag] = load_weekday[curr_day*T - n_lag*T: curr_day*T]
        X_test[0, 1*T*n_lag:2*T*n_lag] = Temp_weekday[curr_day*T - n_lag*T: curr_day*T]
        X_test[0, 2*T*n_lag:3*T*n_lag] = Huminity_weekday[curr_day*T - n_lag*T: curr_day*T]
        X_test[0, 3*T*n_lag:4*T*n_lag] = WindSpeed_weekday[curr_day*T - n_lag*T: curr_day*T]
        X_test[0, 4*T*n_lag:5*T*n_lag] = Day_period[curr_day*T - n_lag*T: curr_day*T]

        y_test = load_weekday[curr_day*T: curr_day *T + T]

        ################### forecast ####################################
        # suppress warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")

        nn = MLPRegressor(hidden_layer_sizes = (50, 50), activation = 'relu', max_iter = 10000)
        rf = RandomForestRegressor(n_estimators = 100)
        lr = LinearRegression(fit_intercept = True, normalize = True)

        rf.fit(X_train, y_train)
        nn.fit(X_train, y_train)
        lr.fit(X_train, y_train)

        y_nn = nn.predict(X_test)
        y_nn = y_nn.flatten()

        y_rf = rf.predict(X_test)
        y_rf = y_rf.flatten()

        y_lr = lr.predict(X_test)
        y_lr = y_lr.flatten()

        '''
        xaxis = range(T)
        plt.figure(figsize=(18,10))
        plt.plot(xaxis, y_test, 'r')
        plt.plot(xaxis, y_rf, 'g')
        plt.show()
        '''
        # statistics of Neural Network
        MAPE_nn = predict_util.calMAPE(y_test, y_nn)
        MAPE_sum_nn += MAPE_nn
        RMSPE_nn = predict_util.calRMSPE(y_test, y_nn)
        RMSPE_sum_nn += RMSPE_nn

        # statistics of Random Forest        
        MAPE_rf = predict_util.calMAPE(y_test, y_rf)
        MAPE_sum_rf += MAPE_rf
        RMSPE_rf = predict_util.calRMSPE(y_test, y_rf)
        RMSPE_sum_rf += RMSPE_rf

        # statistics of Linear Regression
        MAPE_lr = predict_util.calMAPE(y_test, y_lr)
        MAPE_sum_lr += MAPE_lr
        RMSPE_lr = predict_util.calRMSPE(y_test, y_lr)
        RMSPE_sum_lr += RMSPE_lr


    days_sample = n_days - 1 - n_train - n_lag

    MAPE_avg_nn = MAPE_sum_nn / days_sample
    RMSPE_avg_nn = RMSPE_sum_nn / days_sample
    MAPE_avg_rf = MAPE_sum_rf / days_sample
    RMSPE_avg_rf = RMSPE_sum_rf / days_sample
    MAPE_avg_lr = MAPE_sum_lr / days_sample
    RMSPE_avg_lr = RMSPE_sum_lr / days_sample   

    return (MAPE_avg_nn, RMSPE_avg_nn, MAPE_avg_rf, RMSPE_avg_rf, MAPE_avg_lr, RMSPE_avg_lr)

    
if __name__ == "__main__": 
    
    bld_names = ['combined/1008_EE_CSE', 'combined/1108_Chem', 'combined/1111_Fluke', 'combined/1126_Meany', 'combined/1143_McMahon', 'combined/1147_Haggett', 'combined/1158_McCarty', 'combined/1163_Port_Bay', 'combined/1195_Hec_Ed', 'combined/1201_Gowen', 'combined/1275_Pool', 'combined/1306_Physics', 'combined/1316_BAEEC', 'combined/1357_Fish_Sc', 'combined/4057_Foege']
    T = 96;
    # number of days in training set    
    n_train = 50
    # number of lags
    n_lag = 5
    
    nn_MAPE = []
    nn_RMSPE = []
    rf_MPAE = []
    rf_RMSPE = []
    lr_MAPE = []
    lr_RMSPE = []
    

    for bld_name in bld_names:
        print(bld_name)
        load_weekday = getWeekday.getWeekdayload(bld_name)
        (Temp_weekday, Huminity_weekday, WindSpeed_weekday, Day_period) = load_weather.getWeatherData(bld_name)
        (MAPE_avg_nn, RMSPE_avg_nn, MAPE_avg_rf, RMSPE_avg_rf, MAPE_avg_lr, RMSPE_avg_lr) = forecast_multifeather(bld_name, load_weekday, n_train, n_lag, Temp_weekday, Huminity_weekday, WindSpeed_weekday, Day_period)
        nn_MAPE.append(MAPE_avg_nn)
        nn_RMSPE.append(RMSPE_avg_nn)
        rf_MPAE.append(MAPE_avg_rf)
        rf_RMSPE.append(RMSPE_avg_rf)
        lr_MAPE.append(MAPE_avg_lr)
        lr_RMSPE.append(RMSPE_avg_lr)
        
    d = dict({'bld_name' : bld_names, 'nn_MAPE' : nn_MAPE, 'nn_RMSPE' : nn_RMSPE, 'rf_MPAE' : rf_MPAE, 'rf_RMSPE' : rf_RMSPE, 'lr_MAPE' : lr_MAPE, 'lr_RMSPE' : lr_RMSPE})
    df = pd.DataFrame(d)    
    df.to_csv('result\multifeature_forecast_results.csv', sep=',', index = False)
    