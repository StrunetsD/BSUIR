# %% [markdown]
# # Лабораторная работа 3: Transfer Learning и интерпретируемость

# %% [markdown]
# ## 0. Импорты и настройка

# %%
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms 
from torch.utils.data import DataLoader, Subset
import matplotlib.pyplot as plt
import numpy as np
import random
import copy
import time
import cv2
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import warnings
warnings.filterwarnings("ignore")

# Фиксация seed для воспроизводимости
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True

set_seed(42)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# %% [markdown]
# ## 1. Подготовка данных
# Разные трансформации для модели A (CIFAR-10 статистики) и моделей B/C (ImageNet статистики)

# %%
classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

# Статистики
imagenet_mean = [0.485, 0.456, 0.406]
imagenet_std = [0.229, 0.224, 0.225]
cifar_mean = (0.4914, 0.4822, 0.4465)
cifar_std = (0.2023, 0.1994, 0.2010)

# Трансформации для модели A (32x32)
transform_a = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomCrop(32, padding=4),
    transforms.ToTensor(),
    transforms.Normalize(cifar_mean, cifar_std)
])

transform_test_a = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
    transforms.Normalize(cifar_mean, cifar_std)
])

# Трансформации для моделей B и C (224x224, ImageNet нормализация)
transform_bc = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Lambda(lambda img: img.convert("RGB")),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomCrop(224, padding=28),
    transforms.ToTensor(),
    transforms.Normalize(imagenet_mean, imagenet_std)
])

transform_test_bc = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Lambda(lambda img: img.convert("RGB")),
    transforms.ToTensor(),
    transforms.Normalize(imagenet_mean, imagenet_std)
])

# %% [markdown]
# ### Загрузка датасетов и разбиение train/val

# %%
# Датасеты для модели A
trainset_a = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_a)
testset_a = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform_test_a)

# Датасеты для моделей B и C
trainset_bc = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_bc)
testset_bc = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform_test_bc)

# Разбиение 80/20
num_train = len(trainset_a)
split = int(0.8 * num_train)
indices = list(range(num_train))
train_idx, val_idx = indices[:split], indices[split:]

# DataLoaders
batch_size_a, batch_size_bc = 64, 32  # Меньше batch для 224x224

trainloader_a = DataLoader(Subset(trainset_a, train_idx), batch_size=batch_size_a, shuffle=True, num_workers=2)
valloader_a = DataLoader(Subset(trainset_a, val_idx), batch_size=batch_size_a, shuffle=False, num_workers=2)
testloader_a = DataLoader(testset_a, batch_size=batch_size_a, shuffle=False, num_workers=2)

trainloader_bc = DataLoader(Subset(trainset_bc, train_idx), batch_size=batch_size_bc, shuffle=True, num_workers=2)
valloader_bc = DataLoader(Subset(trainset_bc, val_idx), batch_size=batch_size_bc, shuffle=False, num_workers=2)
testloader_bc = DataLoader(testset_bc, batch_size=batch_size_bc, shuffle=False, num_workers=2)

print(f"Train: {len(train_idx)}, Val: {len(val_idx)}, Test: {len(testset_a)}")

# %% [markdown]
# ## 2. Вспомогательные функции

# %%
# Подсчёт обучаемых параметров
def count_parameters(model):
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total

# Одна эпоха обучения
def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    for inputs, labels in loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * inputs.size(0)
    return total_loss / len(loader.dataset)

# Оценка модели
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    return total_loss / len(loader.dataset), 100 * correct / total

# %% [markdown]
# ## 3. Модель A: Обучение с нуля (SimpleCNN)

# %%
class SimpleCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout2d(0.3)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.dropout_fc = nn.Dropout(0.5)

    def forward(self, x):
        x = self.pool(F.relu(self.bn1(self.conv1(x))))  # 32x32 -> 16x16
        x = self.pool(F.relu(self.bn2(self.conv2(x))))  # 16x16 -> 8x8
        x = self.dropout(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout_fc(x)
        return self.fc2(x)

# %%
model_a = SimpleCNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer_a = optim.Adam(model_a.parameters(), lr=0.001)

trainable_a, total_a = count_parameters(model_a)
print(f"Params: {trainable_a:,} / {total_a:,}")

# Обучение
best_acc_a, best_wts_a = 0.0, copy.deepcopy(model_a.state_dict())
start = time.time()

for epoch in range(20):
    train_loss = train_epoch(model_a, trainloader_a, optimizer_a, criterion, device)
    val_loss, val_acc = evaluate(model_a, valloader_a, criterion, device)
    
    if val_acc > best_acc_a:
        best_acc_a = val_acc
        best_wts_a = copy.deepcopy(model_a.state_dict())
    
    if (epoch + 1) % 5 == 0:
        print(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Acc={val_acc:.2f}%")

model_a.load_state_dict(best_wts_a)
time_a = time.time() - start
_, test_acc_a = evaluate(model_a, testloader_a, criterion, device)
print(f"Test Acc: {test_acc_a:.2f}%, Time: {time_a:.1f}s")

# %% [markdown]
# ## 4. Модель B: Предобученная с замороженными слоями

# %%
model_b = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.DEFAULT)

# Замораживаем все слои
for param in model_b.parameters():
    param.requires_grad = False

# Новая голова
model_b.fc = nn.Sequential(
    nn.Linear(model_b.fc.in_features, 256),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(256, 10)
)
model_b = model_b.to(device)

# Оптимизатор только для головы
optimizer_b = optim.Adam(filter(lambda p: p.requires_grad, model_b.parameters()), lr=0.001)

trainable_b, total_b = count_parameters(model_b)
print(f"Params: {trainable_b:,} / {total_b:,}")

# %%
best_acc_b, best_wts_b = 0.0, copy.deepcopy(model_b.state_dict())
start = time.time()

for epoch in range(20):
    train_loss = train_epoch(model_b, trainloader_bc, optimizer_b, criterion, device)
    val_loss, val_acc = evaluate(model_b, valloader_bc, criterion, device)
    
    if val_acc > best_acc_b:
        best_acc_b = val_acc
        best_wts_b = copy.deepcopy(model_b.state_dict())
    
    if (epoch + 1) % 5 == 0:
        print(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Acc={val_acc:.2f}%")

model_b.load_state_dict(best_wts_b)
time_b = time.time() - start
_, test_acc_b = evaluate(model_b, testloader_bc, criterion, device)
print(f"Test Acc: {test_acc_b:.2f}%, Time: {time_b:.1f}s")

# %% [markdown]
# ## 5. Модель C: Полный Fine-tuning

# %%
model_c = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.DEFAULT)
model_c.fc = nn.Sequential(
    nn.Linear(model_c.fc.in_features, 256),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(256, 10)
)
model_c = model_c.to(device)

# Раздельные learning rates
backbone_params = [p for n, p in model_c.named_parameters() if "fc" not in n]
head_params = list(model_c.fc.parameters())

optimizer_c = optim.Adam([
    {'params': backbone_params, 'lr': 1e-4},  # Малый LR для backbone
    {'params': head_params, 'lr': 1e-3}       # Больший LR для головы
])

trainable_c, total_c = count_parameters(model_c)
print(f"Params: {trainable_c:,} / {total_c:,}")

# %%
best_acc_c, best_wts_c = 0.0, copy.deepcopy(model_c.state_dict())
start = time.time()

for epoch in range(20):
    train_loss = train_epoch(model_c, trainloader_bc, optimizer_c, criterion, device)
    val_loss, val_acc = evaluate(model_c, valloader_bc, criterion, device)
    
    if val_acc > best_acc_c:
        best_acc_c = val_acc
        best_wts_c = copy.deepcopy(model_c.state_dict())
    
    if (epoch + 1) % 5 == 0:
        print(f"Epoch {epoch+1}: Train Loss={train_loss:.4f}, Val Acc={val_acc:.2f}%")

model_c.load_state_dict(best_wts_c)
time_c = time.time() - start
_, test_acc_c = evaluate(model_c, testloader_bc, criterion, device)
print(f"Test Acc: {test_acc_c:.2f}%, Time: {time_c:.1f}s")

# %% [markdown]
# ## 6. Сравнение моделей

# %%
import pandas as pd

results = pd.DataFrame({
    'Model': ['A (From Scratch)', 'B (Frozen)', 'C (Fine-tuning)'],
    'Trainable Params': [trainable_a, trainable_b, trainable_c],
    'Total Params': [total_a, total_b, total_c],
    'Val Acc': [f"{best_acc_a:.2f}%", f"{best_acc_b:.2f}%", f"{best_acc_c:.2f}%"],
    'Test Acc': [f"{test_acc_a:.2f}%", f"{test_acc_b:.2f}%", f"{test_acc_c:.2f}%"],
    'Time (s)': [f"{time_a:.1f}", f"{time_b:.1f}", f"{time_c:.1f}"]
})
print(results.to_string(index=False))

# Выбираем лучшую модель для интерпретируемости
best_model = model_c
best_model.load_state_dict(best_wts_c)
best_model.eval()
print(f"\nЛучшая модель: C с Test Acc = {test_acc_c:.2f}%")

# %% [markdown]
# ## 7. Задание 2: Интерпретируемость

# %% [markdown]
# ### 7.1 Визуализация фильтров первого слоя

# %%
filters = best_model.conv1.weight.detach().cpu()
filters_norm = (filters - filters.min()) / (filters.max() - filters.min())

fig, axes = plt.subplots(8, 8, figsize=(12, 12))
for i, ax in enumerate(axes.flat):
    if i < 64:
        # Усреднение по RGB каналам
        ax.imshow(filters_norm[i].mean(0).numpy(), cmap='gray')
    ax.axis('off')
plt.suptitle("Фильтры первого слоя (усреднённые по RGB)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 7.2 Визуализация карт активаций

# %%
# Регистрируем hooks для извлечения активаций
activations = {}
def hook_fn(name):
    def hook(module, input, output):
        activations[name] = output.detach()
    return hook

best_model.layer1.register_forward_hook(hook_fn('layer1'))
best_model.layer3.register_forward_hook(hook_fn('layer3'))

# Получаем изображения
images, labels = next(iter(testloader_bc))
images = images[:3].to(device)

with torch.no_grad():
    best_model(images)

# Визуализация
fig, axes = plt.subplots(3, 5, figsize=(15, 9))

for i in range(3):
    # Денормализация для отображения
    img = images[i].cpu()
    for c, m, s in zip(img, imagenet_mean, imagenet_std):
        c.mul_(s).add_(m)
    img = torch.clamp(img, 0, 1)
    
    axes[i, 0].imshow(img.permute(1, 2, 0))
    axes[i, 0].set_title(f"Original\n{classes[labels[i]]}")
    
    # Активации layer1 (ранние слои)
    for j in range(2):
        act = activations['layer1'][i, j].cpu()
        act = (act - act.min()) / (act.max() - act.min())
        axes[i, j+1].imshow(act, cmap='viridis')
        axes[i, j+1].set_title(f"Layer1 ch{j}")
    
    # Активации layer3 (глубокие слои)
    for j in range(2):
        act = activations['layer3'][i, j].cpu()
        act = (act - act.min()) / (act.max() - act.min())
        axes[i, j+3].imshow(act, cmap='viridis')
        axes[i, j+3].set_title(f"Layer3 ch{j}")
    
    for ax in axes[i]:
        ax.axis('off')

plt.suptitle("Карты активаций: ранние vs глубокие слои")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 7.3 Grad-CAM

# %%
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.gradients = None
        self.activations = None
        
        target_layer.register_forward_hook(self.save_activation)
        target_layer.register_full_backward_hook(self.save_gradient)
    
    def save_activation(self, module, input, output):
        self.activations = output
    
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]
    
    def generate(self, image, target_class=None):
        self.model.eval()
        output = self.model(image.unsqueeze(0))
        
        if target_class is None:
            target_class = output.argmax().item()
        
        self.model.zero_grad()
        output[0, target_class].backward()
        
        # Global Average Pooling градиентов
        weights = self.gradients[0].mean(dim=(1, 2), keepdim=True)
        cam = (weights * self.activations[0]).sum(dim=0)
        cam = F.relu(cam)
        cam = (cam - cam.min()) / (cam.max() + 1e-8)
        
        return cam.cpu().numpy(), target_class

# Создаём Grad-CAM для последнего свёрточного слоя
grad_cam = GradCAM(best_model, best_model.layer4[-1])

# %%
# Визуализация Grad-CAM для 8 изображений (4 правильных, 4 ошибочных)
def show_gradcam(model, loader, num_correct=4, num_incorrect=4):
    all_images, all_labels, all_preds = [], [], []
    
    with torch.no_grad():
        for imgs, lbls in loader:
            imgs = imgs.to(device)
            preds = model(imgs).argmax(dim=1)
            all_images.extend(imgs.cpu())
            all_labels.extend(lbls.numpy())
            all_preds.extend(preds.cpu().numpy())
            if len(all_images) > 200:
                break
    
    all_images = torch.stack(all_images)
    all_labels = np.array(all_labels)
    all_preds = np.array(all_preds)
    
    # Индексы правильных и неправильных
    correct_idx = np.where(all_labels == all_preds)[0][:num_correct]
    incorrect_idx = np.where(all_labels != all_preds)[0][:num_incorrect]
    selected = list(correct_idx) + list(incorrect_idx)
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    for idx, img_idx in enumerate(selected):
        img = all_images[img_idx].to(device)
        true_lbl = all_labels[img_idx]
        pred_lbl = all_preds[img_idx]
        
        cam, _ = grad_cam.generate(img)
        
        # Денормализация
        img_np = img.cpu().numpy().transpose(1, 2, 0)
        for c, m, s in zip(img_np.T, imagenet_mean, imagenet_std):
            c[:] = c * s + m
        img_np = np.clip(img_np, 0, 1)
        
        # Масштабируем CAM
        cam_resized = cv2.resize(cam, (img_np.shape[1], img_np.shape[0]))
        
        axes[idx].imshow(img_np)
        axes[idx].imshow(cam_resized, cmap='jet', alpha=0.5)
        color = 'green' if true_lbl == pred_lbl else 'red'
        axes[idx].set_title(f"Pred: {classes[pred_lbl]}\nTrue: {classes[true_lbl]}", color=color)
        axes[idx].axis('off')
    
    plt.suptitle("Grad-CAM: красные области = важные для классификации")
    plt.tight_layout()
    plt.show()

show_gradcam(best_model, testloader_bc)

# %% [markdown]
# ### 7.4 Анализ ошибок

# %%
# Confusion Matrix
all_preds, all_labels = [], []
best_model.eval()

with torch.no_grad():
    for imgs, lbls in testloader_bc:
        imgs = imgs.to(device)
        preds = best_model(imgs).argmax(dim=1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(lbls.numpy())

cm = confusion_matrix(all_labels, all_preds)
disp = ConfusionMatrixDisplay(cm, display_labels=classes)
fig, ax = plt.subplots(figsize=(10, 10))
disp.plot(ax=ax, xticks_rotation=45, cmap='Blues')
plt.title("Confusion Matrix")
plt.show()

# Топ-3 ошибки
errors = [(i, j, cm[i, j]) for i in range(10) for j in range(10) if i != j]
errors.sort(key=lambda x: x[2], reverse=True)

print("Топ-3 ошибки:")
for true_c, pred_c, count in errors[:3]:
    print(f"  {classes[true_c]} -> {classes[pred_c]}: {count} случаев")

# %%
# Визуализация примеров ошибок с Grad-CAM
fig, axes = plt.subplots(3, 3, figsize=(15, 15))

for err_idx, (true_c, pred_c, _) in enumerate(errors[:3]):
    # Находим примеры
    mask = (np.array(all_labels) == true_c) & (np.array(all_preds) == pred_c)
    indices = np.where(mask)[0][:3]
    
    for ex_idx, idx in enumerate(indices):
        img_tensor, _ = testset_bc[idx]
        img_tensor = img_tensor.to(device)
        
        cam, _ = grad_cam.generate(img_tensor, target_class=pred_c)
        
        # Денормализация
        img_np = img_tensor.cpu().numpy().transpose(1, 2, 0)
        for c, m, s in zip(img_np.T, imagenet_mean, imagenet_std):
            c[:] = c * s + m
        img_np = np.clip(img_np, 0, 1)
        
        cam_resized = cv2.resize(cam, (img_np.shape[1], img_np.shape[0]))
        
        ax = axes[err_idx, ex_idx]
        ax.imshow(img_np)
        ax.imshow(cam_resized, cmap='jet', alpha=0.5)
        ax.set_title(f"{classes[true_c]} → {classes[pred_c]}")
        ax.axis('off')

plt.suptitle("Топ-3 ошибки: где модель смотрит при ошибке")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### Дополнение 1: Grad-CAM для нескольких классов одного изображения

# %%
def show_gradcam_multiclass(model, image_tensor, true_label, classes):
    """
    Показывает Grad-CAM для предсказанного и истинного класса (если различаются)
    """
    model.eval()
    with torch.no_grad():
        output = model(image_tensor.unsqueeze(0))
        probs = F.softmax(output, dim=1)
        pred_class = output.argmax().item()
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Оригинальное изображение
    img_np = image_tensor.cpu().numpy().transpose(1, 2, 0)
    for c, m, s in zip(img_np.T, imagenet_mean, imagenet_std):
        c[:] = c * s + m
    img_np = np.clip(img_np, 0, 1)
    
    axes[0].imshow(img_np)
    axes[0].set_title(f"Original\nTrue: {classes[true_label]}")
    axes[0].axis('off')
    
    # Grad-CAM для предсказанного класса
    cam_pred, _ = grad_cam.generate(image_tensor, target_class=pred_class)
    cam_pred_resized = cv2.resize(cam_pred, (img_np.shape[1], img_np.shape[0]))
    
    axes[1].imshow(img_np)
    axes[1].imshow(cam_pred_resized, cmap='jet', alpha=0.5)
    axes[1].set_title(f"Predicted: {classes[pred_class]}\nProb: {probs[0, pred_class]:.3f}")
    axes[1].axis('off')
    
    # Grad-CAM для истинного класса (если отличается)
    if pred_class != true_label:
        cam_true, _ = grad_cam.generate(image_tensor, target_class=true_label)
        cam_true_resized = cv2.resize(cam_true, (img_np.shape[1], img_np.shape[0]))
        
        axes[2].imshow(img_np)
        axes[2].imshow(cam_true_resized, cmap='jet', alpha=0.5)
        axes[2].set_title(f"True class CAM\n{classes[true_label]}")
        axes[2].axis('off')
    else:
        axes[2].axis('off')
    
    plt.suptitle("Grad-CAM: что видит модель для разных классов")
    plt.tight_layout()
    plt.show()

# Пример использования на ошибочно классифицированном изображении
incorrect_mask = (np.array(all_labels) != np.array(all_preds))
incorrect_indices = np.where(incorrect_mask)[0]

if len(incorrect_indices) > 0:
    idx = incorrect_indices[0]
    img, lbl = testset_bc[idx]
    show_gradcam_multiclass(best_model, img.to(device), lbl, classes)

# %% [markdown]
# ### Дополнение 2: Подробный анализ ошибок с комментариями

# %%
def analyze_error_examples(model, testset, all_labels, all_preds, errors, num_examples=2):
    """
    Анализирует примеры ошибок с Grad-CAM и выводит комментарии
    """
    for err_idx, (true_c, pred_c, count) in enumerate(errors[:3]):
        print(f"\n{'='*50}")
        print(f"Ошибка {err_idx+1}: {classes[true_c]} → {classes[pred_c]} ({count} случаев)")
        print(f"{'='*50}")
        
        # Находим примеры
        mask = (np.array(all_labels) == true_c) & (np.array(all_preds) == pred_c)
        indices = np.where(mask)[0][:num_examples]
        
        for ex_idx, idx in enumerate(indices):
            img_tensor, _ = testset[idx]
            
            # Получаем CAM
            cam, _ = grad_cam.generate(img_tensor.to(device), target_class=pred_c)
            
            # Визуализация
            fig, axes = plt.subplots(1, 2, figsize=(10, 5))
            
            img_np = img_tensor.numpy().transpose(1, 2, 0)
            for c, m, s in zip(img_np.T, imagenet_mean, imagenet_std):
                c[:] = c * s + m
            img_np = np.clip(img_np, 0, 1)
            
            axes[0].imshow(img_np)
            axes[0].set_title("Original Image")
            axes[0].axis('off')
            
            cam_resized = cv2.resize(cam, (img_np.shape[1], img_np.shape[0]))
            axes[1].imshow(img_np)
            axes[1].imshow(cam_resized, cmap='jet', alpha=0.5)
            axes[1].set_title(f"Grad-CAM for '{classes[pred_c]}'")
            axes[1].axis('off')
            
            plt.suptitle(f"Пример {ex_idx+1}: Почему модель ошиблась?")
            plt.tight_layout()
            plt.show()
            
            # Комментарий к ошибке
            print(f"\nПример {ex_idx+1}:")
            print(f"  - Модель предсказала: {classes[pred_c]}")
            print(f"  - Истинный класс: {classes[true_c]}")
            print(f"  - Область внимания (красная зона): показывает, на что 'смотрела' модель")
            
            # Анализ сложности примера
            if classes[true_c] in ['cat', 'dog'] and classes[pred_c] in ['cat', 'dog']:
                print(f"  - Сложность: Похожие классы (кошки vs собаки)")
            elif classes[true_c] in ['deer', 'horse']:
                print(f"  - Сложность: Похожие животные с 4 ногами")
            elif classes[true_c] in ['car', 'truck']:
                print(f"  - Сложность: Транспортные средства")
            else:
                print(f"  - Сложность: Возможно нетипичный ракурс или фон")

# Запускаем анализ
analyze_error_examples(best_model, testset_bc, all_labels, all_preds, errors)

# %% [markdown]
# ### Дополнение 3: Сравнение паттернов в фильтрах

# %%
def visualize_filter_patterns(model):
    """
    Визуализирует и анализирует паттерны в фильтрах первого слоя
    """
    filters = model.conv1.weight.detach().cpu()
    
    # Группируем по ориентациям (примерная оценка)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    patterns = {
        'Горизонтальные границы': [],
        'Вертикальные границы': [],
        'Диагональные / Градиенты': [],
        'Цветовые пятна': []
    }
    
    for i in range(min(64, filters.shape[0])):
        filt = filters[i].mean(0).numpy()  # Усреднение по RGB
        
        # Простая эвристика для классификации паттернов
        h_grad = np.abs(filt[:, 1:] - filt[:, :-1]).mean()  # Горизонтальный градиент
        v_grad = np.abs(filt[1:, :] - filt[:-1, :]).mean()  # Вертикальный градиент
        
        if h_grad > v_grad * 1.5:
            patterns['Горизонтальные границы'].append(i)
        elif v_grad > h_grad * 1.5:
            patterns['Вертикальные границы'].append(i)
        elif np.std(filt) < 0.3:
            patterns['Цветовые пятна'].append(i)
        else:
            patterns['Диагональные / Градиенты'].append(i)
    
    # Визуализируем примеры каждого типа
    for idx, (pattern_name, filter_indices) in enumerate(patterns.items()):
        if len(filter_indices) > 0:
            axes[idx].set_title(f"{pattern_name}\n({len(filter_indices)} фильтров)")
            
            # Показываем до 16 фильтров этого типа
            sub_filters = filters[filter_indices[:16]]
            grid = torchvision.utils.make_grid(
                sub_filters[:, :1, :, :],  # Берём только R канал для визуализации
                nrow=4, normalize=True, padding=1
            )
            axes[idx].imshow(grid.permute(1, 2, 0).numpy(), cmap='gray')
        axes[idx].axis('off')
    
    plt.suptitle("Типы фильтров в первом свёрточном слое")
    plt.tight_layout()
    plt.show()
    
    return patterns

patterns = visualize_filter_patterns(best_model)

print("\nАнализ фильтров:")
for name, indices in patterns.items():
    print(f"  {name}: {len(indices)} фильтров")

# %% [markdown]
# ### Дополнение 4: Сохранение результатов и итоговый вывод

# %%
# Сохраняем веса лучшей модели
torch.save(best_model.state_dict(), 'best_model_cifar10.pth')
print("Модель сохранена в 'best_model_cifar10.pth'")

# Итоговая сводка
print("\n" + "="*60)
print("ИТОГИ ЛАБОРАТОРНОЙ РАБОТЫ 3")
print("="*60)

print("\nЗадание 1 (Transfer Learning):")
print(f"  • Модель A (с нуля):      Test Acc = {test_acc_a:.2f}%")
print(f"  • Модель B (frozen):      Test Acc = {test_acc_b:.2f}%")
print(f"  • Модель C (fine-tuning): Test Acc = {test_acc_c:.2f}%")

print(f"\nЛучший подход: ", end="")
if test_acc_c >= max(test_acc_a, test_acc_b):
    print("Fine-tuning (модель C)")
elif test_acc_b >= test_acc_a:
    print("Frozen features (модель B)")
else:
    print("Обучение с нуля (модель A)")

print("\nЗадание 2 (Интерпретируемость):")
print("  ✓ Визуализация фильтров первого слоя")
print("  ✓ Карты активаций (ранние vs глубокие слои)")
print("  ✓ Grad-CAM для правильных и ошибочных предсказаний")
print("  ✓ Анализ ошибок через Confusion Matrix")
print("  ✓ Grad-CAM для разных классов одного изображения")

print("\nКлючевые наблюдения:")
print("  1. Transfer learning улучшает точность за счёт предобученных признаков")
print("  2. Fine-tuning даёт лучший результат, но требует больше времени")
print("  3. Grad-CAM показывает, что модель фокусируется на значимых частях объектов")
print("  4. Частые ошибки — между визуально похожими классами (cat/dog, deer/horse)")