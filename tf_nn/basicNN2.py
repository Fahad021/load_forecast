import pandas as pd
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import getWeekday
import predict_util
import time
import glob


#### get a list of buildings #### 
def getBldMap():
    return [str(file[5:-4]) for file in glob.glob('data\*.csv')]


#### add one neural network layer ####
def add_layer(inputs, in_size, out_size, activation_function=None):
    Weights = tf.Variable(tf.random_normal([in_size, out_size]))
    biases = tf.Variable(tf.zeros([1, out_size]) + 0.1)
    Wx_plus_b = tf.matmul(inputs, Weights) + biases
    return (
        Wx_plus_b
        if activation_function is None
        else activation_function(Wx_plus_b)
    )


#### neural network forecast
def NN_forecast(bld_name, sess):
    load_weekday = getWeekday.getWeekdayload(bld_name)
    max_load = np.max(load_weekday)
    n_days = int(load_weekday.size / T)
    ################## generate data ##########################################
    MAPE_sum = 0.0
    RMSPR_sum = 0.0

    # maximum iteration
    Max_iter = 10000
    # stopping criteria
    epsilon = 1e-7
    for curr_day in range(n_train + n_lag, n_days-1):
        y_train = np.zeros((n_train, T))
        X_train = np.zeros((n_train, T * n_lag))
        for row, train_day in enumerate(range(curr_day - n_train, curr_day)):
            y_train[row,:] = load_weekday[train_day * T : train_day * T + T]
            X_train[row,0*T*n_lag:1*T*n_lag] = load_weekday[train_day * T - n_lag * T: train_day * T]
        # building test data
        X_test = np.zeros((1, T * n_lag))
        X_test[0, 0*T*n_lag:1*T*n_lag] = load_weekday[curr_day*T - n_lag*T: curr_day*T]
        y_test = load_weekday[curr_day*T: curr_day *T + T]

        X_train = X_train / max_load
        y_train = y_train / max_load
        X_test = X_test / max_load
        y_test = y_test / max_load

        last_l = 10000

        for _ in range(Max_iter):
            # training
            (t_step, l) = sess.run([train_step, loss], feed_dict={xs: X_train, ys: y_train})
            if(abs(last_l - l) < epsilon): 
                #print(i)
                break
            else:
                last_l = l
                # to see the step improvement
                #print(sess.run(loss, feed_dict={xs: X_train, ys: y_train}))


        #y_ = prediction.eval(session = sess, feed_dict={xs: X_train})
        y_pred = prediction.eval(session = sess, feed_dict={xs: X_test})

        # plot daily forecast
        '''
        T = 96
        xaxis = range(T)
        plt.plot(xaxis, y_pred.flatten(), 'r')
        plt.plot(xaxis, y_test.flatten(), 'g')
        plt.show()
        '''
        mape = predict_util.calMAPE(y_test, y_pred)
        rmspe = predict_util.calRMSPE(y_test, y_pred)
        MAPE_sum += mape
        RMSPR_sum += rmspe

    days_sample = n_days - 1 - n_train - n_lag
    return (MAPE_sum / days_sample, RMSPR_sum / days_sample)

    
if __name__ == "__main__":
    # number of days in training set    
    n_train = 20
    # number of lags
    n_lag = 5
    # time intervals per day
    T= 96
   
    ############################ TensorFlow ###################################    
    # place holders
    xs = tf.placeholder(tf.float32, [None, T * n_lag])
    ys = tf.placeholder(tf.float32, [None, T])
    
    N_neuron = 50
    # hidden layers
    l1 = add_layer(xs, T * n_lag, N_neuron, activation_function=tf.nn.tanh)
    # output layer
    prediction = add_layer(l1, N_neuron, T, None)
    
    # loss function, RMSPE
    loss = tf.reduce_mean(tf.reduce_sum(tf.square(ys - prediction),
                     reduction_indices=[1]))  
    # training step
    train_step = tf.train.AdamOptimizer().minimize(loss)
    
    # init.
    init = tf.global_variables_initializer()
    
    # run
    sess = tf.Session()
    sess.run(init)


    ############################ building data  ############################
    bld_names = getBldMap()

    
    nn_MAPE = []
    nn_RMSPE = []
    for bld_name in bld_names:
        t = time.time()
        print("forecasting building： " + bld_name + "...")
        load_weekday = getWeekday.getWeekdayload(bld_name)
        (MAPE_avg_nn, RMSPE_avg_nn) = NN_forecast(bld_name, sess)
        nn_MAPE.append(MAPE_avg_nn)
        nn_RMSPE.append(RMSPE_avg_nn)
        print('forecast result MAPE: %.2f, RMSPE: %.2f' % (MAPE_avg_nn, RMSPE_avg_nn))
        elapsed = time.time() - t
        print('elapsed time is : %.2f' % elapsed)
        
    d = dict({'bld_name' : bld_names, 'nn_MAPE' : nn_MAPE, 'nn_RMSPE' : nn_RMSPE})
    df = pd.DataFrame(d)    
    df.to_csv('benchmark_forecast_results.csv', sep=',', index = False)
    