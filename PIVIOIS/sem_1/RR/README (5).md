# Расчетная работа

## Цель

Изучить основы теории графов, способы представления графов, базовые алгоритмы для работы с графами

### Задание

Определить число хорд неориентированного графа.

Граф представляется в виде списка смежности (списка инцидентности).

### Ключевые понятия

`Граф` - математическая абстракция реальной системы любой природы, объекты которой обладают парными связями.

`Неориентриванный граф ` - это граф, в котором ребра не имеют направления или ориентации. В неориентированном графе каждое ребро соединяет две вершины и представляет собой неупорядоченную пару вершин.

`Хорда` - ребро графа, не принадлежащее заданному каркасу.

`Каркас` - связный подграф этого графа, содержащий все вершины графа и не имеющий циклов.

`Подграф` - это часть графа, в которой мы берем некоторые его вершины и ребра.

`Связный подграф` - подграф, который не содержит разрезанных вершин (вершин, которые, если удалены из графа вместе со всеми связанными ребрами, приводит к разбиению графа на две или более компонент связности.)

`Список смежности` - это структура данных, которая представляет граф в виде списка, где каждая вершина графа представлена в виде узла списка, а смежные с ней вершины представлены в виде элементов списка, связанных с соответствующим узлом.(В списке смежности для каждой вершины графа создается список, содержащий вершины, с которыми она имеет ребра (т.е. смежные вершины).

`Список инцидентности ` - это структура данных, используемая для представления графа. В списке инцидентности каждой вершине графа соответствует список ребер, инцидентных этой вершине.(В списке инцидентности для каждого ребра графа создается запись, содержащая вершины, которые оно соединяет).

`Дерево ` - это особый случай графа, в котором нет циклов или замкнутых путей.

# Идея решения

Главная идея решения задачи заключается в проверке, является ли заданный граф деревом, и вычислении числа хорд в этом дереве. Для этого используется функция, которая рекурсивно обходит граф в глубину, проверяя условия для дерева.

# Вывод

В результате выполнения расчетной работы были изучены служеющие темы:

-Работа с графами

-Проверка свойств графа

-Рекурсивные алгоритмы: Решение задачи использует рекурсивную функцию для обхода графа в глубину.