#include <iostream>

using namespace std;

typedef struct obj {
	int data;
	struct obj* next;
	struct obj* prev;
};

obj* addToFront(obj* head, int data) {
	obj* ptr_head = new obj;
	ptr_head->data = data;
	ptr_head->next = head;
	return ptr_head;
}

obj* addToBack(obj* tail, int data) {
	obj* ptr_tail = new obj;
	ptr_tail->data = data;
	ptr_tail->next = NULL;
	if (tail == NULL) {
		ptr_tail->prev = NULL;
		return ptr_tail;
	}

	tail->next = ptr_tail;
	ptr_tail->prev = tail;
	return ptr_tail;
}

void viewHead(const obj* head) {
	const obj* current = head;
	while (current != NULL) {
		cout << " " << current->data;
		current = current->next;
	}
}

void viewTail(const obj* tail) {
	const obj* current = tail;
	while (current->prev != NULL) {
		current = current->prev;
	}
	while (current != NULL) {
		cout << " " << current->data;
		current = current->next;
	}
}

obj* pop1(obj* head) {
	obj* curr = head;
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
	return head;
}

obj* pop2(obj* tail) {
	obj* curr = tail;
	int counter = 0;
	while (curr && curr->prev) {
		if (counter % 2 == 0) {
			obj* temp = curr->prev;
			curr->prev = temp->prev;
			if (temp->prev) {
				temp->prev->next = curr;
			}
			delete temp;
		}
		else {
			curr = curr->prev;
		}
		counter++;
	}

	return tail;
}

int getRandom(int max, int min) {
	return min + rand() % (max - min + 1);
}

int main() {
	obj* head = NULL;
	obj* tail = NULL;
	
	head=addToFront(head, 1);
	head=addToFront(head, 2);
	head=addToFront(head, 3);
	head=addToFront(head, 4);

	
	cout << "from head: ";
	viewHead(head);
	cout << endl;

	tail = addToBack(tail, 1);
	tail = addToBack(tail, 2);
	tail = addToBack(tail, 3);
	tail = addToBack(tail, 4);

	cout << "from back: ";
	viewTail(tail);
	cout << endl;
	pop1(head);
	cout << "delete from head: ";
	viewHead(head);
	cout << endl;
	pop2(tail);
	cout << "delete from tail: ";
	viewTail(tail);
}

