#pragma once
#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <cmath>
#include <gtest/gtest.h>
#include <stdexcept>

using namespace std;


class PolynomialOfOneVariable {
  
private:
  vector<int> coefficients;
public:
  PolynomialOfOneVariable(const vector<int>& coefficients) {
    this->coefficients = coefficients;
  };
  PolynomialOfOneVariable () {};
  PolynomialOfOneVariable(pair<PolynomialOfOneVariable, PolynomialOfOneVariable>) {};
  PolynomialOfOneVariable operator +=(const PolynomialOfOneVariable other) ;
  PolynomialOfOneVariable operator +(const PolynomialOfOneVariable other) ;
  PolynomialOfOneVariable operator -=(const PolynomialOfOneVariable other) ;
  PolynomialOfOneVariable operator -(const PolynomialOfOneVariable other) ;
  PolynomialOfOneVariable operator *=(const PolynomialOfOneVariable other) ;
  PolynomialOfOneVariable operator *(const PolynomialOfOneVariable other) ;
  pair<PolynomialOfOneVariable, PolynomialOfOneVariable> operator/(const PolynomialOfOneVariable other);
  bool check_nulls(const PolynomialOfOneVariable polynomial) const  ;
  friend ostream& operator<<(ostream& out, const PolynomialOfOneVariable& coefficients);
  double operator ()(double x);
  double operator [](int degree);
};
