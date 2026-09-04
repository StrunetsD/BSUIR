import torch
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 0. Настройка среды и константы
# ==========================================
# Выбираем видеокарту, если она доступна (NST требует много вычислений, GPU очень желателен)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
torch.manual_seed(42) # Фиксируем сид для воспроизводимости

# Стандартные значения среднего и стандартного отклонения датасета ImageNet.
# Так как мы используем сеть VGG19, обученную на ImageNet, нам ОБЯЗАТЕЛЬНО 
# нужно нормализовать наши картинки точно так же, как они нормализовались при обучении VGG.
imagenet_mean = [0.485, 0.456, 0.406]
imagenet_std = [0.229, 0.224, 0.225]

# ==========================================
# 1. Вспомогательные функции для изображений
# ==========================================
def load_image(path, size=256):
    """Загружает картинку, меняет размер и превращает в тензор, готовый для VGG19."""
    image = Image.open(path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((size, size)), # Изменение размера (чем больше, тем дольше считать)
        transforms.ToTensor(), # Превращает пиксели 0-255 в числа 0.0-1.0
        transforms.Normalize(imagenet_mean, imagenet_std), # Нормализация под ImageNet
    ])
    # unsqueeze(0) добавляет фейковое измерение батча (batch_size=1), так как PyTorch ждет [B, C, H, W]
    return transform(image).unsqueeze(0).to(device)

def denormalize(tensor):
    """Обратный процесс: из нормализованного тензора делает картинку для отрисовки."""
    # Подгоняем размерности для умножения (Broadcasting)
    mean = torch.tensor(imagenet_mean).view(3, 1, 1).to(tensor.device)
    std = torch.tensor(imagenet_std).view(3, 1, 1).to(tensor.device)
    
    img = tensor.clone().squeeze(0) # Убираем измерение батча
    img = img * std + mean # Денормализация: умножаем на std и прибавляем mean
    
    # clamp(0, 1) обрезает значения, которые вышли за пределы [0, 1] в процессе оптимизации.
    # permute(1, 2, 0) меняет порядок осей с [Channels, Height, Width] на [Height, Width, Channels] (нужно для matplotlib)
    return img.clamp(0, 1).permute(1, 2, 0).cpu().detach().numpy()

# ==========================================
# 2. Инициализация модели VGG19
# ==========================================
# Загружаем только часть .features (сверточные слои), так как классификатор в конце нам не нужен.
vgg = models.vgg19(weights=models.VGG19_Weights.DEFAULT).features.to(device).eval()

# Замораживаем веса модели. Мы НЕ будем обучать саму нейросеть!
# Мы будем менять только пиксели генерируемой картинки.
for param in vgg.parameters():
    param.requires_grad = False

# Карты признаков для стиля берем с разных уровней глубины.
# Ранние слои (conv1_1) ловят мелкие мазки и цвета, глубокие (conv5_1) - крупные элементы текстуры.
style_layers = {'conv1_1': 0, 'conv2_1': 5, 'conv3_1': 10, 'conv4_1': 19, 'conv5_1': 28}
# Для контента берем один глубокий слой. Он "видит" общую геометрию (дома, лица), а не цвета пикселей.
content_layers = {'conv4_2': 21} 
all_layers = {**style_layers, **content_layers}

# ==========================================
# 3. Функции извлечения признаков и Матрица Грама
# ==========================================
def get_features(image, model, layers):
    """Прогоняет картинку через VGG и сохраняет выходы с нужных нам слоев."""
    idx_to_name = {v: k for k, v in layers.items()}
    max_idx = max(idx_to_name.keys())
    features = {}
    x = image
    for i, layer in enumerate(model):
        x = layer(x) # Пропускаем тензор через текущий слой
        if i in idx_to_name:
            features[idx_to_name[i]] = x # Если это нужный нам слой, сохраняем его выход
        if i == max_idx: break # Дальше прогонять нет смысла, экономим время
    return features

def gram_matrix(features):
    """
    Считает Матрицу Грама. Это 핵심 (сердце) переноса стиля.
    Матрица Грама показывает корреляцию (связь) между разными фильтрами (каналами) на одном слое.
    Она "убивает" информацию о пространственном расположении (где находится объект), 
    но сохраняет информацию о текстуре (какие цвета и узоры встречаются вместе).
    """
    b, c, h, w = features.shape # batch, channels, height, width
    F_flat = features.view(b, c, h * w) # Сплющиваем высоту и ширину
    # Умножаем матрицу саму на себя (транспонированную). Получаем матрицу [C, C].
    G = torch.bmm(F_flat, F_flat.transpose(1, 2)) 
    return G / (c * h * w) # Нормализуем на размер, чтобы слои с разным кол-вом пикселей имели равный вес

# ==========================================
# 4. Основной цикл переноса стиля
# ==========================================
def run_style_transfer(content_img, style_img, num_steps=300, alpha=1, beta=1e5):
    # Наша генерируемая картинка начинается как копия картинки контента.
    # requires_grad_(True) означает, что PyTorch будет отслеживать градиенты для ЭТОГО тензора (мы его "обучаем").
    generated = content_img.clone().requires_grad_(True)
    
    # Оптимизатор L-BFGS работает для задачи Style Transfer лучше и быстрее классического Adam, 
    # хотя требует передачи функции (closure).
    optimizer = torch.optim.LBFGS([generated], lr=1.0, max_iter=20)
    
    with torch.no_grad():
        # Один раз заранее вычисляем признаки контента и стиля (они не меняются)
        content_features = get_features(content_img, vgg, all_layers)
        style_features = get_features(style_img, vgg, all_layers)
        # Для стиля нам нужны не сами признаки, а их Матрицы Грама
        style_grams = {layer: gram_matrix(style_features[layer]) for layer in style_layers}

    # Веса для слоев стиля. Больший вес на ранних слоях = более детальная текстура.
    style_weights = {'conv1_1': 1.0, 'conv2_1': 0.8, 'conv3_1': 0.5, 'conv4_1': 0.3, 'conv5_1': 0.1}
    
    mean = torch.tensor(imagenet_mean).view(1, 3, 1, 1).to(device)
    std = torch.tensor(imagenet_std).view(1, 3, 1, 1).to(device)

    for step in range(num_steps):
        # L-BFGS требует функцию closure, которая пересчитывает loss несколько раз за один шаг
        def closure():
            optimizer.zero_grad() # Обнуляем старые градиенты
            # Извлекаем признаки из текущей генерируемой картинки
            gen_features = get_features(generated, vgg, all_layers)
            
            # 1. Content Loss (Потеря контента)
            # MSE (среднеквадратичная ошибка) между картами признаков генерируемой картинки и контента
            c_loss = F.mse_loss(gen_features['conv4_2'], content_features['conv4_2'])
            
            # 2. Style Loss (Потеря стиля)
            s_loss = 0
            for layer in style_layers:
                gen_gram = gram_matrix(gen_features[layer]) # Считаем матрицу Грама для генерации
                # Считаем разницу между матрицами Грама генерации и целевого стиля
                s_loss += style_weights[layer] * F.mse_loss(gen_gram, style_grams[layer])
            
            # Общий лосс = (вес контента * лосс контента) + (вес стиля * лосс стиля)
            # Обычно beta (вес стиля) ставят сильно больше (например, 100 000), т.к. значения с_loss и s_loss в разных масштабах
            total_loss = alpha * c_loss + beta * s_loss
            total_loss.backward() # Обратное распространение ошибки (считаем градиенты для ПИКСЕЛЕЙ картинки)
            return total_loss

        # Делаем шаг оптимизации (изменяем пиксели generated_img)
        optimizer.step(closure)
        
        # Защита от "выгорания" цветов. 
        # После обновления градиентов пиксели могут принять неадекватные значения. 
        # Мы денормализуем их, обрезаем все что меньше 0 и больше 1, и нормализуем обратно.
        with torch.no_grad():
            generated.data = (generated.data * std + mean).clamp(0, 1)
            generated.data = (generated.data - mean) / std

        if step % 50 == 0:
            print(f"Step {step} complete")
            
    return generated

# ==========================================
# 5. Отрисовка и запуск
# ==========================================
def show_results(content_tensor, style_tensor, generated_tensor):
    """Денормализует тензоры и выводит их в ряд с помощью Matplotlib."""
    content_img = denormalize(content_tensor)
    style_img = denormalize(style_tensor)
    generated_img = denormalize(generated_tensor)

    plt.figure(figsize=(15, 5))
    
    plt.subplot(1, 3, 1)
    plt.imshow(content_img)
    plt.title('Content Image')
    plt.axis('off')
    
    plt.subplot(1, 3, 2)
    plt.imshow(style_img)
    plt.title('Style Image')
    plt.axis('off')
    
    plt.subplot(1, 3, 3)
    plt.imshow(generated_img)
    plt.title('Generated Image')
    plt.axis('off')

    plt.show()


# Загрузка
content_img = load_image(content_path, size=256)
style_img = load_image(style_path, size=256)

print("Начинаю перенос стиля... Это может занять пару минут.")
# Запуск оптимизации
result_img = run_style_transfer(
    content_img, 
    style_img, 
    num_steps=300, # Количество итераций обновления (больше - стиль ляжет лучше, но дольше ждать)
    alpha=1,       # Вес сохранения оригинального контента (city)
    beta=1e5       # Вес наложения нового стиля (in_the_garden). 1e5 = 100000.
)

show_results(content_img, style_img, result_img)

# Сохранение итогового результата
# Денормализуем, переводим из 0.0-1.0 в 0-255 и сохраняем как картинку
final_image = Image.fromarray((denormalize(result_img) * 255).astype('uint8'))
final_image.save("stylized_output.jpg")
print("Готово! Изображение сохранено как stylized_output.jpg")