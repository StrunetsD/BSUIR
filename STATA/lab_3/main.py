import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report
)
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("="*80)
print("STEP 1: LOADING DATA")
print("="*80)

df = pd.read_csv('insurance.csv')

print(f"\n✓ Dataset shape: {df.shape}")
print(f"\n✓ Data types:")
print(df.dtypes)
print(f"\n✓ Missing values:")
print(df.isnull().sum())
print(f"\n✓ Basic statistics:")
print(df.describe())

# ============================================================================
# STEP 2: PREPROCESSING
# ============================================================================

print("\n" + "="*80)
print("STEP 2: DATA PREPROCESSING")
print("="*80)

# Create target variable
median_charges = df['charges'].median()
df['target'] = (df['charges'] > median_charges).astype(int)

print(f"\n✓ Binary classification by median: {median_charges:.2f}")
print(f"✓ Class distribution:")
print(df['target'].value_counts())

# Detect outliers
print(f"\n✓ Outlier detection (IQR method):")
for col in ['age', 'bmi', 'children', 'charges']:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = len(df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)])
    print(f"  {col:10s}: {outliers:3d} outliers ({outliers/len(df)*100:.2f}%)")

# Prepare features
X = df.drop(['charges', 'target'], axis=1).copy()
y = df['target']

# Encode categorical
print(f"\n✓ Encoding categorical variables (Label Encoding):")
le_sex = LabelEncoder()
le_smoker = LabelEncoder()
le_region = LabelEncoder()

X['sex'] = le_sex.fit_transform(X['sex'])
X['smoker'] = le_smoker.fit_transform(X['smoker'])
X['region'] = le_region.fit_transform(X['region'])

print(f"  sex: {dict(zip(le_sex.classes_, le_sex.transform(le_sex.classes_)))}")
print(f"  smoker: {dict(zip(le_smoker.classes_, le_smoker.transform(le_smoker.classes_)))}")
print(f"  region: {dict(zip(le_region.classes_, le_region.transform(le_region.classes_)))}")

# Scale features
print(f"\n✓ Scaling features (StandardScaler):")
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
print(f"  First row before scaling: {X.iloc[0].to_dict()}")
print(f"  First row after scaling: {X_scaled.iloc[0].to_dict()}")

# Train-test split
print(f"\n✓ Train-test split (80-20 with stratification):")
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

print(f"  Training set: {len(X_train)} samples")
print(f"  Test set: {len(X_test)} samples")
print(f"  Train classes: {dict(y_train.value_counts())}")
print(f"  Test classes: {dict(y_test.value_counts())}")

# ============================================================================
# STEP 3: BUILD & TRAIN MODELS
# ============================================================================

print("\n" + "="*80)
print("STEP 3: BUILDING AND TRAINING MODELS")
print("="*80)

models = {
    'Decision Tree': DecisionTreeClassifier(random_state=42, max_depth=10),
    'KNN (k=5)': KNeighborsClassifier(n_neighbors=5),
    'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
    'Gaussian Naive Bayes': GaussianNB()
}

trained_models = {}
for name, model in models.items():
    print(f"\n✓ Training {name}...")
    model.fit(X_train, y_train)
    trained_models[name] = model
    print(f"  Successfully trained!")

# ============================================================================
# STEP 4: EVALUATE MODELS
# ============================================================================

print("\n" + "="*80)
print("STEP 4: MODEL EVALUATION - ALL METRICS")
print("="*80)

results = {}
predictions = {}

for name, model in trained_models.items():
    print(f"\n{name}:")
    print("-" * 70)
    
    y_pred = model.predict(X_test)
    predictions[name] = y_pred
    
    # Get probabilities
    if hasattr(model, 'predict_proba'):
        y_prob = model.predict_proba(X_test)[:, 1]
    else:
        y_prob = y_pred
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except:
        roc_auc = 0.0
    
    results[name] = {
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'ROC-AUC': roc_auc
    }
    
    print(f"  Accuracy:    {accuracy:.4f} (100% правильных предсказаний)")
    print(f"  Precision:   {precision:.4f} (точность положительных)")
    print(f"  Recall:      {recall:.4f} (полнота - найденные случаи)")
    print(f"  F1-Score:    {f1:.4f} (среднее Precision и Recall)")
    print(f"  ROC-AUC:     {roc_auc:.4f} (компромисс TPR vs FPR)")

# Comparison table
print("\n" + "="*80)
print("METRICS COMPARISON TABLE")
print("="*80)
results_df = pd.DataFrame(results).T
print(results_df.round(4).to_string())

# ============================================================================
# STEP 5: CONFUSION MATRICES
# ============================================================================

print("\n" + "="*80)
print("STEP 5: CONFUSION MATRICES & DETAILED ANALYSIS")
print("="*80)

for name, y_pred in predictions.items():
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    print(f"\n{name}:")
    print("-" * 70)
    print("Confusion Matrix:")
    print(f"                   Predicted Negative  Predicted Positive")
    print(f"Actual Negative              {tn:3d}                {fp:3d}")
    print(f"Actual Positive              {fn:3d}                {tp:3d}")
    
    print(f"\nComponents:")
    print(f"  TP (True Positives):       {tp:3d}  - правильно классифицированы высокие")
    print(f"  TN (True Negatives):       {tn:3d}  - правильно классифицированы низкие")
    print(f"  FP (False Positives):      {fp:3d}  - ошибочно предсказаны высокие")
    print(f"  FN (False Negatives):      {fn:3d}  - ошибочно предсказаны низкие")
    
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    print(f"\nRates:")
    print(f"  TPR (True Positive Rate):  {tpr:.4f}  - доля найденных высоких")
    print(f"  FPR (False Positive Rate): {fpr:.4f}  - доля ошибочно высоких")
    print(f"  Specificity (TNR):         {specificity:.4f}  - доля найденных низких")
    
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=['Low Charges', 'High Charges']))

# ============================================================================
# STEP 6: TRAINING ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("STEP 6: TRAINING ANALYSIS (OVERFITTING CHECK)")
print("="*80)

for name, model in trained_models.items():
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    train_acc = accuracy_score(y_train, y_train_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    gap = train_acc - test_acc
    
    print(f"\n{name}:")
    print(f"  Training Accuracy: {train_acc:.4f}")
    print(f"  Test Accuracy:     {test_acc:.4f}")
    print(f"  Overfitting Gap:   {gap:.4f}")
    
    if gap < 0.05:
        print(f"  Status: ✓ No overfitting")
    elif gap < 0.15:
        print(f"  Status: ⚠️ Mild overfitting")
    else:
        print(f"  Status: ❌ Significant overfitting")

# ============================================================================
# STEP 7: FEATURE IMPORTANCE
# ============================================================================

print("\n" + "="*80)
print("STEP 7: FEATURE IMPORTANCE ANALYSIS")
print("="*80)

# Decision Tree
print("\nDecision Tree - Feature Importance:")
print("-" * 70)
dt_model = trained_models['Decision Tree']
dt_imp = pd.DataFrame({
    'Feature': X_train.columns,
    'Importance': dt_model.feature_importances_
}).sort_values('Importance', ascending=False)
print(dt_imp.to_string(index=False))

# Logistic Regression
print("\n\nLogistic Regression - Feature Coefficients (Importance):")
print("-" * 70)
lr_model = trained_models['Logistic Regression']
lr_imp = pd.DataFrame({
    'Feature': X_train.columns,
    'Coefficient': lr_model.coef_[0],
    'Abs_Coefficient': np.abs(lr_model.coef_[0])
}).sort_values('Abs_Coefficient', ascending=False)
print(lr_imp.to_string(index=False))

print("\nInterpretation:")
print("  + coefficient → признак увеличивает цену")
print("  - coefficient → признак уменьшает цену")
print("  |coefficient| → величина влияния признака")

# ============================================================================
# STEP 8: HYPERPARAMETER TUNING
# ============================================================================

print("\n" + "="*80)
print("BONUS: HYPERPARAMETER TUNING (GridSearchCV)")
print("="*80)

print("\n1. Decision Tree Tuning...")
dt_params = {
    'max_depth': [3, 5, 7, 10],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}
dt_grid = GridSearchCV(DecisionTreeClassifier(random_state=42), 
                       dt_params, cv=5, scoring='f1', n_jobs=-1)
dt_grid.fit(X_train, y_train)
print(f"   Best params: {dt_grid.best_params_}")
print(f"   Best CV F1-score: {dt_grid.best_score_:.4f}")

print("\n2. KNN Tuning...")
knn_params = {
    'n_neighbors': [3, 5, 7, 9],
    'weights': ['uniform', 'distance'],
    'metric': ['euclidean', 'manhattan']
}
knn_grid = GridSearchCV(KNeighborsClassifier(), 
                        knn_params, cv=5, scoring='f1', n_jobs=-1)
knn_grid.fit(X_train, y_train)
print(f"   Best params: {knn_grid.best_params_}")
print(f"   Best CV F1-score: {knn_grid.best_score_:.4f}")

print("\n3. Logistic Regression Tuning...")
lr_params = {
    'C': [0.001, 0.01, 0.1, 1, 10],
    'solver': ['lbfgs', 'liblinear']
}
lr_grid = GridSearchCV(LogisticRegression(random_state=42, max_iter=1000), 
                       lr_params, cv=5, scoring='f1', n_jobs=-1)
lr_grid.fit(X_train, y_train)
print(f"   Best params: {lr_grid.best_params_}")
print(f"   Best CV F1-score: {lr_grid.best_score_:.4f}")

print("\n4. Gaussian Naive Bayes Tuning...")
gnb_params = {'var_smoothing': [1e-9, 1e-8, 1e-7]}
gnb_grid = GridSearchCV(GaussianNB(), gnb_params, cv=5, scoring='f1', n_jobs=-1)
gnb_grid.fit(X_train, y_train)
print(f"   Best params: {gnb_grid.best_params_}")
print(f"   Best CV F1-score: {gnb_grid.best_score_:.4f}")
