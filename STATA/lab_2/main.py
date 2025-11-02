import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PolynomialFeatures
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import warnings
warnings.filterwarnings('ignore')

# Эти библиотеки используются для работы с данными, визуализации, машинного обучения и построения моделей
# pandas/numpy - для обработки табличных данных и вычислений
# matplotlib/seaborn - для построения графиков и визуализации
# sklearn - основной инструмент для машинного обучения (модели, метрики, предобработка)
# warnings - чтобы отключить лишние предупреждения и не загромождать вывод

df = pd.read_csv('insurance.csv')  
print("Размер датасета:", df.shape)
print("\nПервые 5 строк:")
print(df.head())

# Анализ структуры данных помогает понять, с чем мы работаем
# info() показывает типы данных и наличие пропусков
# describe() дает статистическое описание числовых признаков  
# isnull().sum() подсчитывает пропущенные значения в каждом столбце
print("=== ИНФОРМАЦИЯ О ДАТАСЕТЕ ===")
print(df.info())
print("\n=== СТАТИСТИЧЕСКОЕ ОПИСАНИЕ ===")
print(df.describe())
print("\n=== ПРОВЕРКА ПРОПУЩЕННЫХ ЗНАЧЕНИЙ ===")
print(df.isnull().sum())

# Визуальный анализ помогает понять распределение данных и выявить выбросы
# Гистограммы показывают форму распределения переменных
# Boxplot'ы наглядно демонстрируют выбросы (точки за пределами "усов")
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

axes[0,0].hist(df['charges'], bins=30, alpha=0.7, color='skyblue')
axes[0,0].set_title('Распределение медицинских затрат')
axes[0,0].set_xlabel('Затраты')
axes[0,0].set_ylabel('Частота')

axes[0,1].boxplot(df['charges'])
axes[0,1].set_title('Выбросы в медицинских затратах')

axes[0,2].hist(df['age'], bins=20, alpha=0.7, color='lightgreen')
axes[0,2].set_title('Распределение возраста')
axes[0,2].set_xlabel('Возраст')

axes[1,0].hist(df['bmi'], bins=20, alpha=0.7, color='orange')
axes[1,0].set_title('Распределение BMI')
axes[1,0].set_xlabel('BMI')

axes[1,1].boxplot(df['bmi'])
axes[1,1].set_title('Выбросы в BMI')

df['children'].value_counts().sort_index().plot(kind='bar', ax=axes[1,2], color='purple', alpha=0.7)
axes[1,2].set_title('Распределение количества детей')
axes[1,2].set_xlabel('Количество детей')

plt.tight_layout()
plt.show()

# Анализ влияния категориальных переменных на целевую
# Boxplot'ы по категориям показывают различия в распределении затрат
# Scatter plot с цветовым кодированием помогает увидеть взаимодействие признаков
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

sns.boxplot(data=df, x='smoker', y='charges', ax=axes[0,0])
axes[0,0].set_title('Влияние курения на медицинские затраты')

sns.boxplot(data=df, x='sex', y='charges', ax=axes[0,1])
axes[0,1].set_title('Влияние пола на медицинские затраты')

sns.boxplot(data=df, x='region', y='charges', ax=axes[1,0])
axes[1,0].set_title('Влияние региона на медицинские затраты')

sns.scatterplot(data=df, x='age', y='charges', hue='smoker', alpha=0.6, ax=axes[1,1])
axes[1,1].set_title('Зависимость затрат от возраста и курения')

plt.tight_layout()
plt.show()

# Матрица корреляций показывает линейные связи между числовыми переменными
# Значения от -1 до 1, где ближе к 1 - сильная положительная корреляция
# Ближе к -1 - сильная отрицательная, около 0 - слабая связь
plt.figure(figsize=(10, 8))
numeric_df = df[['age', 'bmi', 'children', 'charges']]
sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm', center=0)
plt.title('Матрица корреляций числовых признаков')
plt.show()

print("=== ПРЕДОБРАБОТКА ДАННЫХ ===")

# IQR метод для обнаружения выбросов - стандартный статистический подход
# Выбросы определяются как значения за пределами Q1 - 1.5*IQR и Q3 + 1.5*IQR
def detect_outliers_iqr(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = data[(data < lower_bound) | (data > upper_bound)]
    return outliers

# В медицинских данных выбросы часто несут важную информацию о пациентах с особыми условиями
# Поэтому мы их не удаляем, а используем модели, устойчивые к выбросам
print("Выбросы в charges:", len(detect_outliers_iqr(df['charges'])))
print("Выбросы в bmi:", len(detect_outliers_iqr(df['bmi'])))

# Разделение на признаки (X) и целевую переменную (y) - стандартный подход в ML
X = df.drop('charges', axis=1)
y = df['charges']

# Разделение на train/test необходимо для оценки способности модели обобщать
# test_size=0.2 - 20% данных для тестирования, 80% для обучения
# random_state=42 обеспечивает воспроизводимость результатов
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Размер обучающей выборки: {X_train.shape}")
print(f"Размер тестовой выборки: {X_test.shape}")

# ColumnTransformer позволяет применять разные преобразования к разным типам признаков
numeric_features = ['age', 'bmi', 'children']
categorical_features = ['sex', 'smoker', 'region']

preprocessor = ColumnTransformer(
    transformers=[
        # StandardScaler стандартизирует числовые признаки (среднее=0, std=1)
        ('num', StandardScaler(), numeric_features),
        # OneHotEncoder преобразует категориальные признаки в бинарные
        # drop='first' избегает мультиколлинеарности
        ('cat', OneHotEncoder(drop='first'), categorical_features)
    ])

# fit_transform для обучения, transform для применения преобразований
# Важно не использовать fit на тестовых данных чтобы избежать data leakage
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# Получаем имена признаков после преобразования для интерпретации моделей
cat_encoder = preprocessor.named_transformers_['cat']
feature_names = (numeric_features + 
                list(cat_encoder.get_feature_names_out(categorical_features)))

print("Признаки после предобработки:", feature_names)

# Сравниваем разные типы моделей чтобы выбрать лучший подход
# Линейные модели быстрые и интерпретируемые
# Ансамбли деревьев обычно дают лучшую точность
models = {
    'Linear Regression': LinearRegression(),
    'Ridge Regression': Ridge(alpha=1.0, random_state=42),
    'Lasso Regression': Lasso(alpha=1.0, random_state=42),
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42)
}

# Pipeline объединяет preprocessing и модель в одну цепочку
# Упрощает код
poly_model = Pipeline([
    ('preprocessor', preprocessor),
    ('poly', PolynomialFeatures(degree=2, include_bias=False)),
    ('linear', LinearRegression())
])

models['Polynomial Regression'] = poly_model

# Обучаем все модели и вычисляем метрики на train и test выборках
# Сравнение train/test метрик помогает выявить переобучение
results = []

for name, model in models.items():
    if name == 'Polynomial Regression':
        # PolynomialFeatures уже содержит preprocessing, поэтому используем исходные данные
        model.fit(X_train, y_train)
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
    else:
        model.fit(X_train_processed, y_train)
        y_pred_train = model.predict(X_train_processed)
        y_pred_test = model.predict(X_test_processed)
    
    # MAE - средняя абсолютная ошибка, интерпретируемая метрика
    # MSE/RMSE - штрафуют за большие ошибки
    # R² - доля объясненной дисперсии, основная метрика для сравнения
    train_mae = mean_absolute_error(y_train, y_pred_train)
    train_mse = mean_squared_error(y_train, y_pred_train)
    train_rmse = np.sqrt(train_mse)
    train_r2 = r2_score(y_train, y_pred_train)
    
    test_mae = mean_absolute_error(y_test, y_pred_test)
    test_mse = mean_squared_error(y_test, y_pred_test)
    test_rmse = np.sqrt(test_mse)
    test_r2 = r2_score(y_test, y_pred_test)
    
    results.append({
        'Model': name,
        'Train MAE': train_mae, 'Train MSE': train_mse, 'Train RMSE': train_rmse, 'Train R2': train_r2,
        'Test MAE': test_mae, 'Test MSE': test_mse, 'Test RMSE': test_rmse, 'Test R2': test_r2
    })

# Сводная таблица позволяет сравнить все модели по разным метрикам
results_df = pd.DataFrame(results)
print("=== СРАВНИТЕЛЬНАЯ ТАБЛИЦА МОДЕЛЕЙ ===")
print(results_df.round(4))

# Визуализация помогает быстро оценить результаты
plt.figure(figsize=(15, 10))

# R² - основная метрика для сравнения качества моделей
plt.subplot(2, 3, 1)
models_names = results_df['Model']
test_r2_scores = results_df['Test R2']
plt.barh(models_names, test_r2_scores, color='lightblue')
plt.xlabel('R2 Score')
plt.title('Сравнение R2 Score (тестовая выборка)')
for i, v in enumerate(test_r2_scores):
    plt.text(v, i, f'{v:.3f}', va='center')

# RMSE показывает среднюю ошибку в исходных единицах измерения
plt.subplot(2, 3, 2)
test_rmse_scores = results_df['Test RMSE']
plt.barh(models_names, test_rmse_scores, color='lightcoral')
plt.xlabel('RMSE')
plt.title('Сравнение RMSE (тестовая выборка)')
for i, v in enumerate(test_rmse_scores):
    plt.text(v, i, f'{v:.0f}', va='center')

# Выбираем лучшую модель по R² на тестовой выборке
best_model_name = results_df.loc[results_df['Test R2'].idxmax(), 'Model']
best_model = models[best_model_name]

if best_model_name == 'Polynomial Regression':
    y_pred_best = best_model.predict(X_test)
else:
    y_pred_best = best_model.predict(X_test_processed)

# График предсказаний vs фактов показывает, насколько хорошо модель предсказывает
plt.subplot(2, 3, 3)
plt.scatter(y_test, y_pred_best, alpha=0.6)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Фактические значения')
plt.ylabel('Предсказанные значения')
plt.title(f'Предсказания vs Факты ({best_model_name})')

# Распределение ошибок должно быть нормальным для хорошей модели
plt.subplot(2, 3, 4)
errors = y_pred_best - y_test
plt.hist(errors, bins=30, alpha=0.7, color='orange')
plt.xlabel('Ошибка предсказания')
plt.ylabel('Частота')
plt.title('Распределение ошибок предсказания')

plt.tight_layout()
plt.show()

# Анализ важности признаков помогает понять, какие факторы влияют на затраты
if hasattr(best_model, 'feature_importances_'):
    # Tree-based модели имеют встроенную важность признаков
    importances = best_model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=True)
    
    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance_df['feature'], feature_importance_df['importance'])
    plt.xlabel('Важность признака')
    plt.title(f'Важность признаков ({best_model_name})')
    plt.show()
    
elif best_model_name == 'Polynomial Regression':
    # Для полиномиальной регрессии смотрим коэффициенты
    coefficients = best_model.named_steps['linear'].coef_
    poly_features = best_model.named_steps['poly'].get_feature_names_out(
        best_model.named_steps['preprocessor'].get_feature_names_out()
    )
    
    feature_importance_df = pd.DataFrame({
        'feature': poly_features,
        'coefficient': coefficients
    }).sort_values('coefficient', key=abs, ascending=False).head(10)
    
    print("Топ-10 самых важных полиномиальных признаков:")
    print(feature_importance_df)
else:
    # Линейные модели: коэффициенты показывают влияние признаков
    if best_model_name in ['Linear Regression', 'Ridge Regression', 'Lasso Regression']:
        coefficients = best_model.coef_
        feature_importance_df = pd.DataFrame({
            'feature': feature_names,
            'coefficient': coefficients
        }).sort_values('coefficient', key=abs, ascending=False)
        
        plt.figure(figsize=(10, 6))
        colors = ['red' if x < 0 else 'blue' for x in feature_importance_df['coefficient']]
        plt.barh(feature_importance_df['feature'], feature_importance_df['coefficient'], color=colors)
        plt.xlabel('Коэффициент')
        plt.title(f'Коэффициенты признаков ({best_model_name})')
        plt.show()

# Настройка гиперпараметров может улучшить качество модели
print("=== НАСТРОЙКА ГИПЕРПАРАМЕТРОВ ===")

if best_model_name == 'Gradient Boosting':
    # GridSearchCV перебирает комбинации параметров и выбирает лучшую
    param_grid = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.05, 0.1, 0.15],
        'max_depth': [3, 4, 5]
    }
    
    grid_search = GridSearchCV(
        GradientBoostingRegressor(random_state=42),
        param_grid,
        cv=5,
        scoring='r2',
        n_jobs=-1
    )
    
    grid_search.fit(X_train_processed, y_train)
    
    print("Лучшие параметры:", grid_search.best_params_)
    print("Лучший R2 score:", grid_search.best_score_)
    
    best_tuned_model = grid_search.best_estimator_
    y_pred_tuned = best_tuned_model.predict(X_test_processed)
    
    tuned_r2 = r2_score(y_test, y_pred_tuned)
    print(f"R2 на тестовой выборке после тюнинга: {tuned_r2:.4f}")

# Кросс-валидация дает более надежную оценку качества модели
print("\n=== КРОСС-ВАЛИДАЦИЯ ===")
cv_scores = {}

for name, model in models.items():
    if name != 'Polynomial Regression':
        scores = cross_val_score(model, X_train_processed, y_train, 
                               cv=5, scoring='r2')
        cv_scores[name] = scores
    else:
        scores = cross_val_score(model, X_train, y_train, 
                               cv=5, scoring='r2')
        cv_scores[name] = scores
    
    # mean ± 2*std показывает диапазон качества модели на разных фолдах
    print(f"{name}: R2 = {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")