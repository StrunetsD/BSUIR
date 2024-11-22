import networkx as nx
import matplotlib.pyplot as plt
from networkx import is_eulerian

class Graph:
    def __init__(self):
        self.graph = nx.Graph()

    def add_node(self, node):
        self.graph.add_node(node)

    def print_nodes(self):
        return list(self.graph.nodes())

    def add_edge(self, node1, node2):
        self.graph.add_edge(node1, node2)

    def print_edges(self):
        return list(self.graph.edges())

    def is_eulerian(self):
        return is_eulerian(self.graph)

    def find_all_paths(self, source, target):
        return list(nx.all_simple_paths(self.graph, source=source, target=target))

    def find_shortest_path(self, source, target):
        return nx.shortest_path(self.graph, source=source, target=target)

    def find_shortest_path_length(self, source, target):
        return nx.shortest_path_length(self.graph, source=source, target=target)

    def calculate_distance(self, node1, node2):
        return nx.shortest_path_length(self.graph, source=node1, target=node2)

    def find_eulerian_circuit(self):
        return list(nx.eulerian_circuit(self.graph))

    def minimum_spanning_tree(self):
        return nx.minimum_spanning_tree(self.graph)

    def to_tree(self):
        return self.minimum_spanning_tree()

    def find_subgraph(self, nodes):
        subgraph_nodes = [node for node in nodes if node in self.graph.nodes()]
        return self.graph.subgraph(subgraph_nodes)

    def remove_node(self, node):
        if node in self.graph:
            self.graph.remove_node(node)
        else:
            print(f"Узел {node} не найден в графе.")

    def remove_edge(self, node1, node2):
        if self.graph.has_edge(node1, node2):
            self.graph.remove_edge(node1, node2)
        else:
            print(f"Ребро между {node1} и {node2} не найдено в графе.")

    def draw_graph(self):
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', node_size=2000, font_size=15)
        plt.title("Граф")
        plt.show()


class DirectedGraph(Graph):
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_edge(self, node1, node2):
        self.graph.add_edge(node1, node2)

    def print_edges(self):
        return list(self.graph.edges())

    def find_all_paths(self, source, target):
        return list(nx.all_simple_paths(self.graph, source=source, target=target))

    def find_shortest_path(self, source, target):
        return nx.shortest_path(self.graph, source=source, target=target)

    def find_shortest_path_length(self, source, target):
        return nx.shortest_path_length(self.graph, source=source, target=target)

    def calculate_distance(self, node1, node2):
        return nx.shortest_path_length(self.graph, source=node1, target=node2)

    def draw_graph(self):
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_color='lightgreen', node_size=2000, font_size=15, arrows=True)
        plt.title("Ориентированный граф")
        plt.show()


def main():
    print("Выбор типа графа:")
    print("1. Неориентированный граф")
    print("2. Ориентированный граф")
    choice = input("Выберите тип графа (1 или 2): ")

    if choice == '1':
        g = Graph()
    elif choice == '2':
        g = DirectedGraph()
    else:
        print("Неверный выбор. Выход...")
        return

    while True:
        print("\nКоманды:")
        print("1. Добавить узел")
        print("2. Добавить ребро")
        print("3. Удалить узел")
        print("4. Удалить ребро")
        print("5. Показать узлы")
        print("6. Показать ребра")
        print("7. Проверить, является ли граф эйлеровым")
        print("8. Найти все пути")
        print("9. Найти кратчайший путь")
        print("10. Найти длину кратчайшего пути")
        print("11. Найти эйлеров цикл (только для неориентированного графа)")
        print("12. Минимальное остовное дерево (только для неориентированного графа)")
        print("13. Найти подграф")
        print("14. Перевести граф в дерево (только для неориентированного графа)")
        print("15. Нарисовать граф")
        print("16. Выход")

        choice = input("Выберите команду (1-16): ")

        if choice == '1':
            node = input("Введите узел: ")
            g.add_node(node)
            print(f"Узел {node} добавлен.")

        elif choice == '2':
            node1 = input("Введите первый узел: ")
            node2 = input("Введите второй узел: ")
            g.add_edge(node1, node2)
            print(f"Ребро между {node1} и {node2} добавлено.")

        elif choice == '3':
            node = input("Введите узел для удаления: ")
            g.remove_node(node)

        elif choice == '4':
            node1 = input("Введите первый узел: ")
            node2 = input("Введите второй узел: ")
            g.remove_edge(node1, node2)

        elif choice == '5':
            print("Узлы графа:", g.print_nodes())

        elif choice == '6':
            print("Ребра графа:", g.print_edges())

        elif choice == '7':
            print("Граф является эйлеровым:", g.is_eulerian() if isinstance(g, Graph) else "Ориентированные графы не могут быть эйлеровыми.")

        elif choice == '8':
            source = input("Введите начальный узел: ")
            target = input("Введите конечный узел: ")
            paths = g.find_all_paths(source, target)
            print("Все пути между узлами:", paths)

        elif choice == '9':
            source = input("Введите начальный узел: ")
            target = input("Введите конечный узел: ")
            try:
                path = g.find_shortest_path(source, target)
                print("Кратчайший путь:", path)
            except nx.NetworkXNoPath:
                print("Нет пути между узлами.")

        elif choice == '10':
            source = input("Введите начальный узел: ")
            target = input("Введите конечный узел: ")
            try:
                length = g.find_shortest_path_length(source, target)
                print("Длина кратчайшего пути:", length)
            except nx.NetworkXNoPath:
                print("Нет пути между узлами.")

        elif choice == '11':
            if isinstance(g, Graph) and g.is_eulerian():
                circuit = g.find_eulerian_circuit()
                print("Эйлеров цикл:", circuit)
            else:
                print("Граф не является эйлеровым или это ориентированный граф.")

        elif choice == '12':
            if isinstance(g, Graph):
                mst = g.minimum_spanning_tree()
                print("Минимальное остовное дерево:", list(mst.edges(data=True)))
            else:
                print("Это ориентированный граф. Минимальное остовное дерево не доступно.")

        elif choice == '13':
            nodes = input("Введите узлы подграфа через запятую: ").split(',')
            subgraph = g.find_subgraph(nodes)
            print("Подграф:")
            print("Узлы подграфа:", list(subgraph.nodes()))
            print("Ребра подграфа:", list(subgraph.edges()))

        elif choice == '14':
            if isinstance(g, Graph):
                tree = g.to_tree()
                print("Граф переведен в дерево (минимальное остовное дерево):")
                print("Узлы дерева:", list(tree.nodes()))
                print("Ребра дерева:", list(tree.edges(data=True)))
            else:
                print("Это ориентированный граф. Перевод в дерево не доступен.")

        elif choice == '15':
            g.draw_graph()

        elif choice == '16':
            print("Выход...")
            break

        else:
            print("Неверный выбор. Пожалуйста, выберите команду от 1 до 16.")

if __name__ == '__main__':
    main()