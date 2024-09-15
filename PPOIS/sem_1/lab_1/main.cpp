#include "PolynomialOfOneVariable.h"


int main() {
  vector<int> coeffs1 = {1,1,2}; 
  vector<int> coeffs2 = {1,2}; 
  PolynomialOfOneVariable test_1(coeffs1);
  PolynomialOfOneVariable test_2(coeffs2);
  PolynomialOfOneVariable test_sum = test_1 + test_2;
  PolynomialOfOneVariable test_4 = test_1 - test_2;
  PolynomialOfOneVariable test_5 = test_1 * test_2;
  cout<<"first: "<<test_1<<endl;
  cout<<"second: "<<test_2<<endl;
  cout<<"sum: "<<test_sum<<endl;
  cout<<"minus: "<<test_4<<endl;
  cout<<"proizved: "<<test_5<<endl;
  auto result = test_1 / test_2;
  cout << "whole part :" << result.first << "\n" << "remainder: " << result.second<<"\n";
  testing::InitGoogleTest();
  return RUN_ALL_TESTS();

}
// g++ -o main PolynomialOfOneVariable.cpp main.cpp TEST.cpp -lgtest -lgtest_main
// ./main --gtest_output=json:result.json

