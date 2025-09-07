import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

folders = ['histograms', 'boxplots', 'barplots', 'correlation', 
           'scatter_plots', 'contingency_tables', 'additional_visualizations']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

df = pd.read_csv('HR_Data_MNC_Data_Science_Lovers.csv')

print("="*50)
print("1. ИЗУЧЕНИЕ СТРУКТУРЫ ДАННЫХ")
print("="*50)

print(f"Размер датасета: {df.shape[0]} строк и {df.shape[1]} столбцов")
print("\nПервые 5 строк данных:")
print(df.head())
print("\nПоследние 5 строк данных:")
print(df.tail())
print("\nИнформация о датасете:")
print(df.info())
print("\nСтатистическое описание числовых переменных:")
print(df.describe())

print("\n" + "="*50)
print("2. ПРЕДОБРАБОТКА ДАННЫХ")
print("="*50)

print("Пропущенные значения:")
missing_values = df.isnull().sum()
print(missing_values[missing_values > 0])

if missing_values.sum() > 0:
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            if df[col].dtype == 'object':
                df[col].fillna(df[col].mode()[0], inplace=True)
            else:
                df[col].fillna(df[col].median(), inplace=True)
    print("Пропущенные значения обработаны")


duplicates_count = df.duplicated().sum()
print(f"\nКоличество полных дубликатов: {duplicates_count}")

if duplicates_count > 0:
    df = df.drop_duplicates()
    print(f"Удалено {duplicates_count} дубликатов")

print("\nАнализ выбросов для числовых столбцов:")
numeric_cols = df.select_dtypes(include=[np.number]).columns

for col in numeric_cols:
    if col != 'Unnamed: 0':  
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        print(f"{col}: {len(outliers)} выбросов ({len(outliers)/len(df)*100:.2f}%)")

print("\nПреобразование типов данных:")
df['Hire_Date'] = pd.to_datetime(df['Hire_Date'])
print("Столбец Hire_Date преобразован в datetime")


df['Years_in_Company'] = (pd.Timestamp.now() - df['Hire_Date']).dt.days / 365.25
df['Years_in_Company'] = df['Years_in_Company'].round(1)

df['Salary_Category'] = pd.cut(df['Salary_INR'], 
                              bins=[0, 800000, 1200000, float('inf')], 
                              labels=['Low', 'Medium', 'High'])

print("Созданы новые переменные: Years_in_Company и Salary_Category")

if 'Unnamed: 0' in df.columns:
    df.drop(columns=['Unnamed: 0'], inplace=True)
    print("Удален технический столбец 'Unnamed: 0'")

print("\n" + "="*50)
print("3. АНАЛИТИЧЕСКИЕ ЗАПРОСЫ")
print("="*50)


# 10 исследовательских вопросов к данным
dept_distribution = df['Department'].value_counts()
print("1. Распределение сотрудников по отделам:")
print(dept_distribution)

avg_salary_by_dept = df.groupby('Department')['Salary_INR'].mean().sort_values(ascending=False)
print("\n2. Средняя зарплата по отделам:")
print(avg_salary_by_dept.round(2))

exp_salary_corr = df['Experience_Years'].corr(df['Salary_INR'])
print(f"\n3. Корреляция между опытом и зарплатой: {exp_salary_corr:.3f}")

hires_by_year = df['Hire_Date'].dt.year.value_counts().sort_index()
print("\n4. Количество наймов по годам:")
print(hires_by_year)

top_positions = df['Job_Title'].value_counts().head(10)
print("\n5. Топ-10 должностей:")
print(top_positions)

status_distribution = df['Status'].value_counts()
print("\n6. Распределение по статусам:")
print(status_distribution)

salary_by_workmode = df.groupby('Work_Mode')['Salary_INR'].mean()
print("\n7. Средняя зарплата по режимам работы:")
print(salary_by_workmode.round(2))

resignations_by_title = df[df['Status'] == 'Resigned']['Job_Title'].value_counts().head(5)
print("\n8. Топ-5 должностей по увольнениям:")
print(resignations_by_title)

performance_salary_corr = df['Performance_Rating'].corr(df['Salary_INR'])
print(f"\n9. Корреляция между рейтингом и зарплатой: {performance_salary_corr:.3f}")

exp_by_dept = df.groupby('Department')['Experience_Years'].mean().sort_values(ascending=False)
print("\n10. Средний опыт работы по отделам:")
print(exp_by_dept.round(2))

print("\n" + "="*50)
print("4. ВИЗУАЛИЗАЦИИ В СООТВЕТСТВИИ С ПУНКТОМ 3.3")
print("="*50)

# ОДНОМЕРНАЯ ВИЗУАЛИЗАЦИЯ

# 1. Гистограммы для количественных переменных (минимум 2)
print("\n1. ГИСТОГРАММЫ ДЛЯ КОЛИЧЕСТВЕННЫХ ПЕРЕМЕННЫХ")

plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='Salary_INR', kde=True, bins=30)
plt.title('Распределение зарплат с кривой плотности')
plt.xlabel('Зарплата (INR)')
plt.ylabel('Частота')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('histograms/salary_histogram.png')
plt.show()


plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='Experience_Years', kde=True, bins=20)
plt.title('Распределение опыта работы с кривой плотности')
plt.xlabel('Опыт работы (лет)')
plt.ylabel('Частота')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('histograms/experience_histogram.png')
plt.show()

plt.figure(figsize=(10, 6))
sns.kdeplot(data=df, x='Salary_INR', fill=True)
plt.title('График плотности распределения зарплат')
plt.xlabel('Зарплата (INR)')
plt.ylabel('Плотность')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('histograms/salary_kde.png')
plt.show()

print("\n2. BOX PLOT ДЛЯ КОЛИЧЕСТВЕННЫХ ПЕРЕМЕННЫХ")

plt.figure(figsize=(8, 6))
sns.boxplot(y=df['Salary_INR'])
plt.title('Распределение зарплат (boxplot)')
plt.ylabel('Зарплата (INR)')
plt.tight_layout()
plt.savefig('boxplots/salary_boxplot.png')
plt.show()

plt.figure(figsize=(8, 6))
sns.boxplot(y=df['Experience_Years'])
plt.title('Распределение опыта работы (boxplot)')
plt.ylabel('Опыт работы (лет)')
plt.tight_layout()
plt.savefig('boxplots/experience_boxplot.png')
plt.show()

plt.figure(figsize=(8, 6))
sns.violinplot(y=df['Salary_INR'])
plt.title('Скрипичная диаграмма зарплат')
plt.ylabel('Зарплата (INR)')
plt.tight_layout()
plt.savefig('boxplots/salary_violin.png')
plt.show()

print("\n3. BAR PLOT ДЛЯ КАТЕГОРИАЛЬНЫХ ПЕРЕМЕННЫХ")

plt.figure(figsize=(12, 6))
sns.countplot(data=df, x='Department')
plt.title('Распределение сотрудников по отделам')
plt.xlabel('Отдел')
plt.ylabel('Количество сотрудников')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('barplots/department_barchart.png')
plt.show()

plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='Status')
plt.title('Распределение сотрудников по статусам')
plt.xlabel('Статус')
plt.ylabel('Количество сотрудников')
plt.tight_layout()
plt.savefig('barplots/status_barchart.png')
plt.show()

plt.figure(figsize=(10, 6))
sns.countplot(data=df, y='Work_Mode', order=df['Work_Mode'].value_counts().index)
plt.title('Распределение по режимам работы')
plt.xlabel('Количество сотрудников')
plt.ylabel('Режим работы')
plt.tight_layout()
plt.savefig('barplots/workmode_barchart.png')
plt.show()

# МНОГОМЕРНАЯ ВИЗУАЛИЗАЦИЯ
print("\n4. CORRELATION MATRIX ДЛЯ КОЛИЧЕСТВЕННЫХ ПЕРЕМЕННЫХ")

# Вычисление корреляций
numeric_cols = ['Salary_INR', 'Experience_Years', 'Performance_Rating', 'Years_in_Company']
corr_matrix = df[numeric_cols].corr()

# Тепловая карта корреляций
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, fmt='.3f', cbar_kws={'label': 'Коэффициент корреляции'})
plt.title('Матрица корреляций количественных переменных')
plt.tight_layout()
plt.savefig('correlation/correlation_matrix.png')
plt.show()

# 2. Scatter plot для пар количественных переменных (минимум 2)
print("\n5. SCATTER PLOT ДЛЯ ПАР КОЛИЧЕСТВЕННЫХ ПЕРЕМЕННЫХ")

plt.figure(figsize=(10, 6))
sns.regplot(data=df, x='Experience_Years', y='Salary_INR', scatter_kws={'alpha':0.6})
plt.title('Зависимость зарплаты от опыта работы с линией тренда')
plt.xlabel('Опыт работы (лет)')
plt.ylabel('Зарплата (INR)')
plt.tight_layout()
plt.savefig('scatter_plots/experience_salary_scatter.png')
plt.show()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df.sample(1000), x='Performance_Rating', y='Salary_INR', 
                hue='Department', size='Experience_Years', alpha=0.7)
plt.title('Зависимость зарплаты от рейтинга производительности')
plt.xlabel('Рейтинг производительности')
plt.ylabel('Зарплата (INR)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('scatter_plots/performance_salary_scatter.png')
plt.show()

numeric_cols = df.select_dtypes(include=[np.number]).columns
sns.pairplot(df[numeric_cols].sample(1000), diag_kind='hist')
plt.suptitle('Матрица диаграмм рассеяния количественных переменных', y=1.02)
plt.tight_layout()
plt.savefig('scatter_plots/pairplot_matrix.png')
plt.show()

print("\n6. CONTINGENCY TABLE С ВИЗУАЛИЗАЦИЕЙ ДЛЯ КАТЕГОРИАЛЬНЫХ ПЕРЕМЕННЫХ")

# Создание таблицы сопряженности
contingency_table = pd.crosstab(df['Department'], df['Status'])

plt.figure(figsize=(12, 8))
sns.heatmap(contingency_table, annot=True, fmt='d', cmap='Blues')
plt.title('Тепловая карта таблицы сопряженности: Отдел vs Статус')
plt.xlabel('Статус')
plt.ylabel('Отдел')
plt.tight_layout()
plt.savefig('contingency_tables/contingency_heatmap.png')
plt.show()


contingency_table.plot(kind='bar', figsize=(12, 6))
plt.title('Групповая столбчатая диаграмма: Отдел vs Статус')
plt.xlabel('Отдел')
plt.ylabel('Количество сотрудников')
plt.legend(title='Статус')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('contingency_tables/contingency_barchart.png')
plt.show()

print("\n7. ДОПОЛНИТЕЛЬНО: КОЛИЧЕСТВЕННЫЕ ПРОТИВ КАТЕГОРИАЛЬНЫХ ПЕРЕМЕННЫХ")

plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='Department', y='Salary_INR')
plt.title('Распределение зарплат по отделам')
plt.xlabel('Отдел')
plt.ylabel('Зарплата (INR)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('additional_visualizations/salary_by_department_boxplot.png')
plt.show()

plt.figure(figsize=(12, 6))
sns.violinplot(data=df, x='Department', y='Salary_INR')
plt.title('Сравнение распределений зарплат по отделам')
plt.xlabel('Отдел')
plt.ylabel('Зарплата (INR)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('additional_visualizations/salary_by_department_violin.png')
plt.show()

plt.figure(figsize=(12, 6))
sns.stripplot(data=df, x='Status', y='Experience_Years', size=4, alpha=0.7)
plt.title('Точечная диаграмма опыта работы по статусам')
plt.xlabel('Статус')
plt.ylabel('Опыт работы (лет)')
plt.tight_layout()
plt.savefig('additional_visualizations/experience_by_status_strip.png')
plt.show()

print("\n8. КОМПЛЕКСНАЯ ВИЗУАЛИЗАЦИЯ В ОДНОМ ОКНЕ")

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

axes[0, 0].hist(df['Salary_INR'], bins=30, alpha=0.7, edgecolor='black')
axes[0, 0].set_title('Распределение зарплат')
axes[0, 0].set_xlabel('Зарплата (INR)')
axes[0, 0].set_ylabel('Частота')
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].scatter(df['Experience_Years'], df['Salary_INR'], alpha=0.6)
axes[0, 1].set_title('Опыт работы vs Зарплата')
axes[0, 1].set_xlabel('Опыт работы (лет)')
axes[0, 1].set_ylabel('Зарплата (INR)')

df.boxplot(column='Salary_INR', by='Department', ax=axes[1, 0])
axes[1, 0].set_title('Зарплаты по отделам')
axes[1, 0].set_xlabel('Отдел')
axes[1, 0].set_ylabel('Зарплата (INR)')
axes[1, 0].tick_params(axis='x', rotation=45)

df['Department'].value_counts().plot(kind='bar', ax=axes[1, 1])
axes[1, 1].set_title('Распределение по отделам')
axes[1, 1].set_xlabel('Отдел')
axes[1, 1].set_ylabel('Количество сотрудников')
axes[1, 1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('additional_visualizations/comprehensive_visualization.png')
plt.show()

print("\n9. ОПИСАТЕЛЬНАЯ СТАТИСТИКА ДЛЯ КЛЮЧЕВЫХ ПЕРЕМЕННЫХ")

print("Описательная статистика зарплат:")
print(df['Salary_INR'].describe())

print(f"\nМедиана зарплат: {df['Salary_INR'].median():.2f}")
print(f"Мода зарплат: {df['Salary_INR'].mode().values}")
print(f"Коэффициент асимметрии зарплат: {df['Salary_INR'].skew():.3f}")
print(f"Коэффициент эксцесса зарплат: {df['Salary_INR'].kurtosis():.3f}")

print("\nТаблица частот для отделов:")
freq_table = df['Department'].value_counts()
rel_freq = df['Department'].value_counts(normalize=True)
summary_table = pd.DataFrame({
    'Частота': freq_table,
    'Процент': rel_freq * 100
})
print(summary_table)

