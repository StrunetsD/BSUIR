#include <iostream>
#include <string>

using namespace std;

struct Tree {
    string name;
    int age;
    Tree* left, * right;
};

Tree* List(string name, int age) {
    Tree* ptr = new Tree;
    ptr->name = name;
    ptr->age = age;
    ptr->left = ptr->right = NULL;
    return ptr;
}

Tree* take_from_array(Tree* root, string name, int age) {
    if (!root) {
        Tree* ptr_root = new Tree;
        ptr_root->name = name;
        ptr_root->age = age;
        ptr_root->left = ptr_root->right = NULL;
        return ptr_root;
    }
    else if (name < root->name) {
        root->left = take_from_array(root->left, name, age);
    }
    else if (name > root->name) {
        root->right = take_from_array(root->right, name, age);
    }
    return root;
}

Tree* Add_info(Tree* root, int age, string name) {
    if (!root) 
    {
        Tree* ptr1 = new Tree;
        ptr1->age = age;
        ptr1->name = name;
        ptr1->left = 0;
        ptr1->right = 0;
        return ptr1;
    }
    else if (name < root->name) {
        root->right = Add_info(root->right, age, name);
    }
    else if (name > root->name) {
        root->left = Add_info(root->left, age, name);
    }
    return root;
}

void ViewTree(Tree* root, int level) {
    if (!root) {
        return;
    }
    ViewTree(root->right, level + 1);
    for (int i = 0; i < level; i++) {
        cout << "    ";
    }
    cout << root->name << " (" << root->age << ")" << endl;
    ViewTree(root->left, level + 1);
}

Tree* CreateBalancedBST(string names[], int ages[], int start, int end) {
    if (start > end) {
        return NULL;
    }

    int mid = (start + end) / 2;
    Tree* root = List(names[mid], ages[mid]);

    root->left = CreateBalancedBST(names, ages, start, mid - 1);
    root->right = CreateBalancedBST(names, ages, mid + 1, end);

    return root;
}

Tree* Find_el(Tree* root, string name) {
    Tree* ptr2 = NULL;
    if (!root || root->name == name) {
        return root;
    }
    if (ptr2 == NULL && root->left != NULL) {
       Tree* ptr2 = Find_el(root->left, name);
    }
    if (ptr2 == NULL && root->right != NULL) {
        ptr2 = Find_el(root->right, name);
    }

    if (ptr2 != NULL ) {
        cout << "Результат поиска: " << ptr2->name << " (" << ptr2->age << ")" << endl;
    }

    return ptr2;
}

void PreorderTraversal(Tree* root) {
    if (root) {
        cout << "Имя: " << root->name <<", " << "Возраст: " << root->age << endl;
        PreorderTraversal(root->left);
        PreorderTraversal(root->right);
   }
    
}
void InorderTraversal(Tree* root) {
    if (root) {
        InorderTraversal(root->left);
        cout << "Имя: " << root->name << ", " << "Возраст: " << root->age << endl;
        InorderTraversal(root->right);
    }
}

void  PostorderTraversal(Tree* root) {
    if (root) {
        PostorderTraversal(root->left);
        PostorderTraversal(root->right);
        cout << "Имя: " << root->name << ", "<<" Возраст: " << root->age << endl;
    }
}

int Problem(Tree* root) {
    if (!root) {
        return 0;
    }
    return 1 + Problem(root->left);
}

Tree* DeleteNode(Tree* root, string name) {
    if (root == NULL)
        return root;

    if (name == root->name) {

        Tree* tmp;
        if (root->right == NULL)
            tmp = root->left;
        else {

            Tree* ptr = root->right;
            if (ptr->left == NULL) {
                ptr->left = root->left;
                tmp = ptr;
            }
            else {

                Tree* pmin = ptr->left;
                while (pmin->left != NULL) {
                    ptr = pmin;
                    pmin = ptr->left;
                }
                ptr->left = pmin->right;
                pmin->left = root->left;
                pmin->right = root->right;
                tmp = pmin;
            }
        }

        delete root;
        return tmp;
    }
    else if (name < root->name)
        root->left = DeleteNode(root->left, name);
    else
        root->right = DeleteNode(root->right, name);
    return root;
}





void Del_Tree(Tree*& ptr_next) {
    if (ptr_next != NULL) {
        Del_Tree(ptr_next->left);
        Del_Tree(ptr_next->right);
        delete ptr_next;
        ptr_next = NULL;
    }
}

int main() {
    setlocale(LC_ALL,"RUS");
    Tree* root = NULL;
    string names[] = { "Kirill", "Aleksey", "Ann", "Petya", "Max", "Dima","Artem"};
    int ages[] = { 25, 30, 20, 35, 28, 19, 20 };
    int size = sizeof(names) / sizeof(names[0]);
    root = CreateBalancedBST(names, ages, 0, size - 1);
    root = Add_info(root, 40, "Nikita");
    ViewTree(root, 0);
    cout << endl;
    cout << endl;
    DeleteNode(root, "Dima");
    ViewTree(root, 0);
    cout << endl;
    int prob = Problem(root);
    cout <<"Количество записей в левой ветви дерева: "<< prob<< endl;
    cout << endl;
    Find_el(root, "Ann");
    cout << endl;
    cout << "Прямой обход дерева:" << endl;
    PreorderTraversal(root);
    cout << endl;
    cout << "Симметричный обход дерева: " << endl;
    InorderTraversal( root);
    cout << endl;
    cout << "Обратный обход: " << endl;
    PostorderTraversal(root);
    Del_Tree(root);
}
