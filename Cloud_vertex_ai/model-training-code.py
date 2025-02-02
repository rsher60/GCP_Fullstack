import pandas as pd
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from google.cloud import storage
from joblib import dump
from sklearn.pipeline import make_pipeline
import pickle
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import warnings

warnings.filterwarnings('ignore')
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from datetime import datetime

storage_client = storage.Client()
bucket = storage_client.bucket("rsher60-training-bucket")

filename = 'gs://rsher60-training-bucket/Sample-data/credit-score-train.csv'


def load_data(filename):
    df = pd.read_csv(filename, on_bad_lines='skip')
    return df


def preprocess_data(df):
    """
    Cleans and converts specified columns in a Pandas DataFrame.

    Removes hyphens and underscores from multiple columns and replaces a
    specific string in 'Payment_Behaviour'. Then, converts several columns
    to appropriate numerical data types.

    Args:
        data: The input DataFrame.

    Returns:
        The cleaned and converted DataFrame.
    """

    data1 = df.drop(columns=['ID', 'Customer_ID', 'Month', 'Name', 'SSN', 'Monthly_Inhand_Salary',
                             'Type_of_Loan', 'Num_of_Delayed_Payment', 'Amount_invested_monthly'])

    # Deleting (-) and (_) in Column
    data1['Age'] = data1['Age'].str.replace('-', '')
    data1['Age'] = data1['Age'].str.replace('_', '')

    # Deleting (-) and (_) in Column
    data1['Annual_Income'] = data1['Annual_Income'].str.replace('-', '')
    data1['Annual_Income'] = data1['Annual_Income'].str.replace('_', '')

    # Deleting (-) and (_) in Column
    data1['Num_of_Loan'] = data1['Num_of_Loan'].str.replace('-', '')
    data1['Num_of_Loan'] = data1['Num_of_Loan'].str.replace('_', '')

    # Deleting (-) and (_) in Column
    data1['Changed_Credit_Limit'] = data1['Changed_Credit_Limit'].str.replace('-', '0')
    data1['Changed_Credit_Limit'] = data1['Changed_Credit_Limit'].str.replace('_', '0')

    # Deleting (-) and (_) in Column
    data1['Outstanding_Debt'] = data1['Outstanding_Debt'].str.replace('-', '')
    data1['Outstanding_Debt'] = data1['Outstanding_Debt'].str.replace('_', '')

    # Deleting (-) and (_) in Column
    data1['Monthly_Balance'] = data1['Monthly_Balance'].str.replace('-', '')
    data1['Monthly_Balance'] = data1['Monthly_Balance'].str.replace('_', '')

    # Deleting (-) and (_) in Column
    data1['Credit_History_Age'] = data1['Credit_History_Age'].str.replace('-', '')
    data1['Credit_History_Age'] = data1['Credit_History_Age'].str.replace('_', '')

    # Replacing (!@9#%8) to (Unknown) in Column
    data1['Payment_Behaviour'] = data1['Payment_Behaviour'].str.replace('!@9#%8', 'Unknown')

    data1['Age'] = data1['Age'].astype(int)
    data1['Annual_Income'] = data1['Annual_Income'].astype(float)
    data1['Num_of_Loan'] = data1['Num_of_Loan'].astype(int)
    data1['Changed_Credit_Limit'] = data1['Changed_Credit_Limit'].astype(float)
    data1['Outstanding_Debt'] = data1['Outstanding_Debt'].astype(float)
    data1['Monthly_Balance'] = data1['Monthly_Balance'].astype(float)

    # Replacing outlier of Age with Ffill
    data1['Age'].where((data1['Age'] <= 80), np.nan, inplace=True)
    data1['Age'] = data1['Age'].fillna(method='ffill')

    # Handling missing values with mean
    data1['Monthly_Balance'] = data1['Monthly_Balance'].fillna(data1['Monthly_Balance'].mean())
    data1['Num_Credit_Inquiries'] = data1['Num_Credit_Inquiries'].fillna(data1['Num_Credit_Inquiries'].mean())

    # Handling missing values with ffill
    data1['Occupation'] = data1['Occupation'].replace('_______', method='ffill')
    data1['Credit_Mix'] = data1['Credit_Mix'].replace('_', method='bfill')
    data1 = data1.dropna()

    df = label_encode(data1)
    x = df.drop('Credit_Score', axis=1)
    y = df['Credit_Score']

    return x, y


def label_encode(df):
    le_dict = {}

    a = str(datetime.now()).strip('')

    # Get categorical columns efficiently
    categorical = df.select_dtypes(include='object').columns

    # Apply Label Encoding to all categorical columns at once using apply
    # df[categorical] = df[categorical].apply(le.fit_transform)

    for col in categorical:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        le_dict[col] = dict(zip(le.classes_, le.transform(le.classes_)))  # Store the fitted encoder

    # Save the file to the same location as the job lib file
    artifact_name = f'label_encoder_{a}.pkl'

    with open(artifact_name, 'wb') as f:
        pickle.dump(le_dict, f)

    return df


def train_model(x_train, y_train):
    model = DecisionTreeClassifier(random_state=1)
    pipeline = make_pipeline(model)
    pipeline.fit(x_train, y_train)
    return pipeline


def save_model_artifact(pipeline):
    a = str(datetime.now()).strip('')

    artifact_name = f'model_{a}.joblib'
    dump(pipeline, artifact_name)
    model_artifact = bucket.blob('credit-card-training/' + artifact_name)
    model_artifact.upload_from_filename(artifact_name)


def main():
    filename = "gs://rsher60-training-bucket/Sample-data/credit-score-train.csv"
    df = load_data(filename)
    X, y = preprocess_data(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    pipeline = train_model(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    save_model_artifact(pipeline)
    acc = accuracy_score(y_test, y_pred)
    a = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    print(report)


if __name__ == '__main__':
    main()

