#include <iostream>

using namespace std;

unsigned long long factorial(int n) {
	if (n == 0) {
		return 1;
	}
	else {
		return n * factorial(n - 1);
	}
}

unsigned long long binom(int n, int k) {
	if (k == 0 || n == 0) {
		return 1;
	}
	else {
		return factorial(n) / (factorial(k) * factorial(n - k));
	}
}

unsigned long long function(int n) {
	if (n == 0) {
		return 1;
	}
	else {
		unsigned long long result = 1;
		for (int i = 1; i <= n; i++) {
			result *= i;
		}
		return result;
	}
}

unsigned long long binom1(int n, int k) {
	if (k == 0 || n == 0) {
		return 1;
	}
	else {
		return function(n) / (function(k) * function(n - k));
	}
}

int main() {
	int n = 10;
	int k = 8;
	unsigned long long result = binom(n, k);
	unsigned long long result1 = binom1(n, k);
	cout << result << endl;
	cout << result1 << endl;
	//СДЕЛАЙ БЛОК-СХЕМУ!!!!!!!!!!!

	
}