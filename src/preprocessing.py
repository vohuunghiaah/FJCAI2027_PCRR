from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def make_preprocessor(X, scaled=True):
    nums = list(X.select_dtypes('number').columns)
    cats = [c for c in X if c not in nums]
    steps = [('imputer', SimpleImputer(strategy='median', keep_empty_features=True))]
    if scaled: steps.append(('scale', StandardScaler()))
    return ColumnTransformer([
        ('numeric', Pipeline(steps), nums),
        ('categorical', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent', keep_empty_features=True)),
            ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), cats)
    ], sparse_threshold=0)
