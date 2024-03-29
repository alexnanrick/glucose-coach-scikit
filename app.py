import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from flask import Flask,request, jsonify
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pandas.tools.plotting import scatter_matrix
from sklearn import model_selection
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import BayesianRidge
from sklearn.externals import joblib

app = Flask(__name__)

BASE = declarative_base()

"""
Classes for ORM
"""


class Users(BASE):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    username = Column('u_username', String(30))
    password = Column('u_password_hash', String(30))
    email = Column('u_email', String(30))
    firstname = Column('u_firstname', String(30))
    weight = Column('u_weight', Float)
    height = Column('u_height', Integer)
    date_created = Column('u_date_created', DateTime)
    profile_image_path = Column('u_profile_image_path', String(100))

# Load dataset
input_file = "blood-glucose-results.csv"
dataset = pd.read_csv(input_file, header = 0)

# Load dir
model_directory = 'model'
model_prefix = '/model_user_'
model_ext = '.pkl'


def get_input_from_json(input_json):
    return np.array(
        [[
            input_json['pf_time_of_day'],
            input_json['bg_value'],
            input_json['food_value'],
            input_json['exercise_value'],
            input_json['ins_value']
        ]]
    )


@app.route('/predict', methods=['POST'])
def predict():
    user_id = str(request.get_json()['userid'])

    model_file_name = model_directory + model_prefix + user_id + model_ext
    clf = joblib.load(model_file_name)

    X = get_input_from_json(request.json)

    predicition = clf.predict(X)[0]

    return jsonify(predicition)


@app.route('/train', methods=['POST'])
def train():
    user_id = str(request.get_json()['userid'])

    #print_csv_details()
    #show_graphs()
    compare_algos()

    # Split-out validation dataset
    array = dataset.values
    x = array[:, 0:4]
    y = array[:, 4]
    validation_size = 0.20
    seed = 7
    x_train, x_validation, y_train, y_validation = model_selection.train_test_split(x, y, test_size=validation_size,
                                                                                    random_state=seed)

    lr = LinearRegression()
    lr.fit(x_train, y_train)
    predictions = lr.predict(x_validation)
    print(predictions)

    model_file_name = model_directory + model_prefix + user_id + model_ext
    joblib.dump(lr, model_file_name)

    return 'Success'


def print_csv_details():
    # shape
    print(dataset.shape)

    # head
    print(dataset.head(20))

    # descriptions
    print(dataset.describe())

    # class distribution
    print(dataset.groupby('pf_time_of_day').size())


def show_graphs():
    # box and whisker plots
    dataset.plot(kind='box', subplots=True, layout=(3, 2), sharex=False, sharey=False)
    plt.show()

    # histograms
    dataset.hist()
    plt.show()

    # scatter plot matrix
    scatter_matrix(dataset)
    plt.show()


def compare_algos():
    # Split-out validation dataset
    array = dataset.values
    X = array[:, 0:4]
    Y = array[:, 4]
    validation_size = 0.20
    seed = 7
    X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(X, Y, test_size=validation_size,
                                                                                    random_state=seed)

    # Spot Check Algorithms
    models = []
    models.append(('LR', LinearRegression()))
    models.append(('RID', Ridge()))
    models.append(('LAS', Lasso()))
    models.append(('EN', ElasticNet()))
    models.append(('BR', BayesianRidge()))

    # evaluate each model in turn
    results = []
    names = []
    for name, model in models:
        cv_results = model_selection.cross_val_score(model, X_train, Y_train)
        results.append(cv_results)
        names.append(name)
        msg = "%s: %f (%f)" % (name, cv_results.mean(), cv_results.std())
        print(msg)

    # Compare Algorithms
    fig = plt.figure()
    fig.suptitle('Algorithm Comparison')
    ax = fig.add_subplot(111)
    plt.boxplot(results)
    ax.set_xticklabels(names)
    plt.show()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)