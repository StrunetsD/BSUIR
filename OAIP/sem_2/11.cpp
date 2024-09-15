#include <iostream>
#include <ctime>

using namespace std;

 struct obj {
	int data;
	struct obj* next;
};

obj* push(obj* top,int data) {
	obj* ptr = new obj;
	ptr->data = data;
	ptr->next = top;
	return ptr;

}
void view(const obj* top) {
	const obj* current = top;
		while (current != NULL) {
			cout << " " << current->data;
			current = current->next;
		}
}

obj* pop(obj* top) {
	obj* curr = top;
	int counter = 1;
	while (curr && curr->next) {
		if (counter % 2 != 0) {
			obj* temp = curr->next;
			curr->next = temp->next;
			delete temp;
		}
		else {
			curr = curr->next;
		}
		counter++;
	}
	return top;
}

void sorting(obj* top) {
	obj* ptr1 = NULL;
	obj* ptr2 = NULL;
	int r;
	bool swapped;
	do {
		swapped = false;
		ptr2 = top;
		while (ptr2->next != ptr1) {
			if (ptr2->data > ptr2->next->data) {
				r = ptr2->data;
				ptr2->data = ptr2->next->data;
				ptr2->next->data = r;
				swapped = true;
			}
			ptr2 = ptr2->next;
		}
	} while (swapped);
}

int getRandom(int max, int min) {
	return min + rand() % (max - min + 1);
}
int main() {
	obj* top = NULL;
	srand(time(NULL));
	int min = -10;
	int max = 10;
	int size = 4;
	for (int i = 0; i < size; i++) {
		int Num = getRandom(min, max);
		top = push(top, Num);
	}
	cout << "before: ";
	view(top);
	cout << endl;
	pop(top);
	cout << "after: ";
	view(top);
	cout << endl;
	sorting(top);
	cout << "sort: ";
	view(top);

}