import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import PolynomialFeatures, OneHotEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import re

# Загрузка данных
df = pd.read_csv('netflix.csv')

# Предобработка duration - извлечь число минут из строки '90 min'
df['duration_min'] = df['duration'].str.extract(r'(\d+)').astype(float)

# Выбор признаков (категориальные и числовые)
features = ['type', 'country', 'release_year', 'rating']
target = 'duration_min'

# Удаление строк с пропусками в этих столбцах
df = df.dropna(subset=features + [target])

# Категориальные и числовые признаки для обработки
categorical_features = ['type', 'country', 'rating']
numeric_features = ['release_year']

# Разделение на X и y
X = df[features]
y = df[target]

# Определение трансформера для категориальных признаков (one-hot encoding)
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
        ('num', 'passthrough', numeric_features)
    ])

# Разделение на тренировочную и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Функция для обучения и оценки моделей
def train_and_evaluate(model, model_name):
    # Создаем pipeline с предобработкой и моделью
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)
    print(f'{model_name} Results:')
    print(f'MAE: {mae:.3f}, MSE: {mse:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}')
    print()
    return {'model': model_name, 'MAE': mae, 'MSE': mse, 'RMSE': rmse, 'R2': r2}

# Список моделей для обучения
results = []
results.append(train_and_evaluate(LinearRegression(), 'Linear Regression'))

# Полиномиальная регрессия степени 2
poly_features = PolynomialFeatures(degree=2, include_bias=False)
poly_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('poly', poly_features),
    ('model', LinearRegression())
])
poly_pipeline.fit(X_train, y_train)
y_pred_poly = poly_pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred_poly)
mse = mean_squared_error(y_test, y_pred_poly)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred_poly)
print('Polynomial Regression Results:')
print(f'MAE: {mae:.3f}, MSE: {mse:.3f}, RMSE: {rmse:.3f}, R2: {r2:.3f}\n')
results.append({'model': 'Polynomial Regression', 'MAE': mae, 'MSE': mse, 'RMSE': rmse, 'R2': r2})

results.append(train_and_evaluate(Ridge(), 'Ridge Regression'))
results.append(train_and_evaluate(Lasso(max_iter=10000), 'Lasso Regression'))
results.append(train_and_evaluate(RandomForestRegressor(random_state=42), 'Random Forest'))
results.append(train_and_evaluate(GradientBoostingRegressor(random_state=42), 'Gradient Boosting'))

# Создание сравнительной таблицы результатов
results_df = pd.DataFrame(results)
print('Summary of model performance:')
print(results_df)
