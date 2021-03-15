import pandas as pd
import numpy as np


def linear_regression_train(X_i, Y_i, theta, alpha=0.01):
    """
    Implements gradient descent algorithm for online linear regression.
    Inputs:
        X_i: Numpy column containing the current X variables.
        Y_i: Response variable
        theta: Current estimate of the predictors.
        alpha: Learning rate
    Returns updated theta.
    """
    loss = np.dot(X_i.T, theta) - Y_i - (np.dot(theta.T, theta) * 0.001)
    dJ = np.dot(X_i, loss) * 2
    return theta - alpha * dJ

def linear_regression_test(X_i, Y_i, theta, se_threshold):
    """
    Test if the current data point is not an anomaly.
    Inputs:
        X_i: Numpy column containing the current X variables.
        Y_i: Response variable
        se_threshold: Squared error threshold. Must be greater than 0.
    Returns True if the current data point is not an anomaly else False.
    """
    squared_error = (Y_i - np.dot(X_i.T, theta)) ** 2
    return True if squared_error <= se_threshold else False

def main():
    data = pd.read_csv('data.csv')
    data= data.drop(columns='Class')
    train_X = data.drop(columns=['Previous Speed'])
    train_Y = data['Current Speed'] - data['Previous Speed']
    theta = np.array([[0],[0],[0]])
    for i in range(100):
        X_i = train_X.iloc[i,].to_numpy().reshape((3,-1))
        Y_i = train_Y.iloc[i,]
        theta = linear_regression_train(X_i, Y_i, theta)
    print(theta)





if __name__ == "__main__":
    main()



