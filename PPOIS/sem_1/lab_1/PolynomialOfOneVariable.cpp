#include "PolynomialOfOneVariable.h"


bool PolynomialOfOneVariable::check_nulls(const PolynomialOfOneVariable& polynomial) const {
  for (int i = 0; i < polynomial.coefficients.size(); i++) {
    if (polynomial.coefficients[i] != 0) {
      return false;
    }
  }
  return true;
}

PolynomialOfOneVariable PolynomialOfOneVariable:: operator +=(const PolynomialOfOneVariable& other)  {
  int size = max(this->coefficients.size(), other.coefficients.size());
   vector<int> result(size, 0);
  if (this->coefficients.size() < other.coefficients.size()) {
    for (int i = 0; i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i] + other.coefficients[i];
    }
    for (int i = coefficients.size(); i < other.coefficients.size(); i++) {
      result[i] = other.coefficients[i];
    }
  }
  else {
    for (int i = 0; i < other.coefficients.size(); i++) {
      result[i] = this->coefficients[i] + other.coefficients[i];
    }
    for (int i = other.coefficients.size(); i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i];
    }
  }
  this->coefficients = result;
  return *this;
}

PolynomialOfOneVariable PolynomialOfOneVariable::operator +(const PolynomialOfOneVariable& other)  {
  int size = max(this->coefficients.size(), other.coefficients.size());
  vector<int> result(size, 0);
  if (this->coefficients.size() < other.coefficients.size()) {
    for (int i = 0; i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i] + other.coefficients[i];
    }
    for (int i = this->coefficients.size(); i < other.coefficients.size(); i++) {
      result[i] = other.coefficients[i];
    }
  }
  else {
    for (int i = 0; i < other.coefficients.size(); i++) {
      result[i] = this->coefficients[i] + other.coefficients[i];
    }
    for (int i = other.coefficients.size(); i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i];
    }
  }
  return PolynomialOfOneVariable(result);
}

PolynomialOfOneVariable PolynomialOfOneVariable::operator -=(const PolynomialOfOneVariable& other)  {
  int size = max(this->coefficients.size(), other.coefficients.size());
  vector<int> result(size, 0);
  if (this->coefficients.size() < other.coefficients.size()) {
    for (int i = 0; i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i] - other.coefficients[i];
    }
    for (int i = this->coefficients.size(); i < other.coefficients.size(); i++) {
      result[i] = -1 * other.coefficients[i];
    }
  }
  else {
    for (int i = 0; i < other.coefficients.size(); i++) {
      result[i] = this->coefficients[i] - other.coefficients[i];
    }
    for (int i = other.coefficients.size(); i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i];
    }
  }
  this->coefficients = result;
  return *this;
}

PolynomialOfOneVariable PolynomialOfOneVariable::operator -(const PolynomialOfOneVariable& other)  {
  int size = max(this->coefficients.size(), other.coefficients.size());
  vector<int> result(size, 0);
  if (this->coefficients.size() < other.coefficients.size()) {
    for (int i = 0; i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i] - other.coefficients[i];
    }
    for (int i = this->coefficients.size(); i < other.coefficients.size(); i++) {
      result[i] = -1 * other.coefficients[i];
    }
  }
  else {
    for (int i = 0; i < other.coefficients.size(); i++) {
      result[i] = this->coefficients[i] - other.coefficients[i];
    }
    for (int i = other.coefficients.size(); i < this->coefficients.size(); i++) {
      result[i] = this->coefficients[i];
    }
  }


  return PolynomialOfOneVariable(result);
}


PolynomialOfOneVariable PolynomialOfOneVariable::operator *=(const PolynomialOfOneVariable& other)  {
  vector<int> result(this->coefficients.size() + other.coefficients.size() - 1);
  for (int i = 0; i < this->coefficients.size(); i++) {
    for (int j = 0; j < other.coefficients.size(); j++) {
      result[i + j] += this->coefficients[i] * other.coefficients[j];


    }
  }
  this->coefficients = result;
  return *this;
}

PolynomialOfOneVariable PolynomialOfOneVariable::operator *(const PolynomialOfOneVariable& other)   {
  vector<int> result(this->coefficients.size() + other.coefficients.size() - 1);
  for (int i = 0; i < this->coefficients.size(); i++) {
    for (int j = 0; j < other.coefficients.size(); j++) {
      result[i + j] += this->coefficients[i] * other.coefficients[j];
    }
  }
  return PolynomialOfOneVariable(result);
}

pair<PolynomialOfOneVariable, PolynomialOfOneVariable> PolynomialOfOneVariable::operator/(const PolynomialOfOneVariable& other) {
  if (check_nulls(other.coefficients)) {
    throw invalid_argument("division by zero");
    return { PolynomialOfOneVariable(), PolynomialOfOneVariable() };
  }

    if (this->coefficients.size() < other.coefficients.size() or other.coefficients.back() == 0) {
      throw invalid_argument("invalid division");
    }
    vector<int> quotient(coefficients.size() - other.coefficients.size() + 1);
    vector<int> remainder(coefficients);
    for (int i = coefficients.size() - 1; i >= 0; --i) {
      int coefficient = coefficients[i] / other.coefficients.back();
      quotient[i - other.coefficients.size() + 1] = coefficient;

      for (int j = 0; j < other.coefficients.size(); ++j) {
        remainder[i - j] -= coefficient * other.coefficients[other.coefficients.size() - 1 - j];
      }
      
    }
    return  { PolynomialOfOneVariable(quotient), PolynomialOfOneVariable(remainder) };  
}
  


double PolynomialOfOneVariable::operator ()(double x)   {
  double result = 0;
  for (int i = 0; i < this->coefficients.size(); i++) {
    result += pow(x, i) * coefficients[i];
  }
  return result;
}

int PolynomialOfOneVariable::operator [](int degree) {
  if (degree>=this->coefficients.size()) {
    throw out_of_range("out of range.: "+degree);
  }
  return this->coefficients[degree];
}



ostream& operator <<(ostream& out, const PolynomialOfOneVariable& polynomial) {
  string result = "P(x)=";
  if (polynomial.coefficients.empty()) {
    result += "0";
  }
  else if (polynomial.check_nulls(polynomial.coefficients)) {
    result+="0";
  };
  bool first = true;
  for (int i = polynomial.coefficients.size() - 1; i >= 0; i--) {
    if (polynomial.coefficients[i] != 0) {
      if (!first and polynomial.coefficients[i] > 0) {
        result += "+";
      }
      first = false;
      if (i == 0) {
        result += to_string(polynomial.coefficients[i]);
      }
      else if (i == 1) {
        result += to_string(polynomial.coefficients[i]) + "x";
      }

      else {
        result += to_string(polynomial.coefficients[i]) + "x^" + to_string(i);
      }

    }
  }
  out << result;
  return out;
}
