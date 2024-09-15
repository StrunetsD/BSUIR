#include "PolynomialOfOneVariable.h"


TEST(PolynomialTest,AdditionOp){
    PolynomialOfOneVariable p1({1,2});
    PolynomialOfOneVariable p2({2,3});
    p1 += p2;
    EXPECT_EQ(p1[0],3);
    EXPECT_EQ(p1[1],5);

}

TEST(PolynomialTest,AdditionOpDifferentSizes){
    PolynomialOfOneVariable p1({1,2});
    PolynomialOfOneVariable p2({2});
    p1 += p2;
    EXPECT_EQ(p1[0],3);
    EXPECT_EQ(p1[1],2);

}

TEST(PolynomialTest, Addition) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    PolynomialOfOneVariable p2({4, 5, 6});  

    PolynomialOfOneVariable result = p1 + p2;
    EXPECT_EQ(result[0], 5); 
    EXPECT_EQ(result[1], 7);  
    EXPECT_EQ(result[2], 9);  
}

TEST(PolynomialTest, AdditionWithZero) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    PolynomialOfOneVariable p2({0,0,0});  

    PolynomialOfOneVariable result = p1 + p2;
    EXPECT_EQ(result[0], 1); 
    EXPECT_EQ(result[1], 2);  
    EXPECT_EQ(result[2], 3);  
}

TEST(PolynomialTest, AdditionDifferentSizes) {
    PolynomialOfOneVariable p1({0,1,3});     
    PolynomialOfOneVariable p2({2});  

    PolynomialOfOneVariable result = p1 + p2;
    EXPECT_EQ(result[0], 2);  
    EXPECT_EQ(result[1], 1);  
    EXPECT_EQ(result[2], 3); 
}

TEST(PolynomialTest, SubtractionOp) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    PolynomialOfOneVariable p2({4, 5, 6});  

    p1 -= p2;
    EXPECT_EQ(p1[0], -3);  
    EXPECT_EQ(p1[1], -3);  
    EXPECT_EQ(p1[2], -3);  
}

TEST(PolynomialTest, SubtractionOpWithZero) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    PolynomialOfOneVariable p2({0,0,0});  

    p1 -= p2;
    EXPECT_EQ(p1[0], 1);  
    EXPECT_EQ(p1[1], 2);  
    EXPECT_EQ(p1[2], 3);  
}

TEST(PolynomialTest, SubtractionWithZero) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    PolynomialOfOneVariable p2({0,0,0});  

    PolynomialOfOneVariable result = p1 - p2;
    EXPECT_EQ(result[0], 1);  
    EXPECT_EQ(result[1], 2);  
    EXPECT_EQ(result[2], 3);  
}

TEST(PolynomialTest, Subtraction) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    PolynomialOfOneVariable p2({4, 5, 6});  

    PolynomialOfOneVariable result = p1 - p2;
    EXPECT_EQ(result[0], -3);  
    EXPECT_EQ(result[1], -3);  
    EXPECT_EQ(result[2], -3);  
}

TEST(PolynomialTest, MultiplicationOp) {
    PolynomialOfOneVariable p1({1, 2});  
    PolynomialOfOneVariable p2({3, 4});  
    p1 *= p2;
    EXPECT_EQ(p1[0], 3);  
    EXPECT_EQ(p1[1], 10); 
    EXPECT_EQ(p1[2], 8);  
}

TEST(PolynomialTest, MultiplicationOpWithZero) {
    PolynomialOfOneVariable p1({1, 2});  
    PolynomialOfOneVariable p2({0, 0});  
    p1 *= p2;
    EXPECT_EQ(p1[0], 0);  
    EXPECT_EQ(p1[1], 0); 
    EXPECT_EQ(p1[2], 0);  
}

TEST(PolynomialTest, MultiplicationWithDiffSize) {
    PolynomialOfOneVariable p1({1, 1,2});  
    PolynomialOfOneVariable p2({1,2});  
    PolynomialOfOneVariable result = p1 * p2;
    EXPECT_EQ(result[0], 1);  
    EXPECT_EQ(result[1], 3); 
    EXPECT_EQ(result[2], 4);  
    EXPECT_EQ(result[3], 4);
}

TEST(PolynomialTest, MultiplicationWithZero) {
    PolynomialOfOneVariable p1({1, 2});  
    PolynomialOfOneVariable p2({0, 0});  
    PolynomialOfOneVariable result = p1 * p2;
    EXPECT_EQ(result[0], 0);  
    EXPECT_EQ(result[1], 0); 
    EXPECT_EQ(result[2], 0);  
}

TEST(PolynomialTest, Multiplication) {
    PolynomialOfOneVariable p1({1, 2});  
    PolynomialOfOneVariable p2({3, 4});  
    PolynomialOfOneVariable result = p1 * p2;
    EXPECT_EQ(result[0], 3);  
    EXPECT_EQ(result[1], 10); 
    EXPECT_EQ(result[2], 8);  
}

TEST(PolynomialTest, Division) {
    PolynomialOfOneVariable p1({0,1,3});  
    PolynomialOfOneVariable p2({1,2});                                          

    auto [quotient, remainder] = p1 / p2;    
    EXPECT_EQ(quotient[1], 1);     
    EXPECT_EQ(remainder[1], 0);
    EXPECT_EQ(remainder[2], 1);
 
}


TEST(PolynomialTest, DivisionByZeroPolynomial) {
    PolynomialOfOneVariable p1({1, 2, 3}); 
    PolynomialOfOneVariable p2({0});        

    EXPECT_THROW({
        auto result  = p1 / p2;
    }, invalid_argument);  
};



TEST(PolynomialTest, Indexing) {
    PolynomialOfOneVariable p1({1, 2, 3});  

    EXPECT_EQ(p1[0], 1); 
    EXPECT_EQ(p1[1], 2);  
    EXPECT_EQ(p1[2], 3);  

    EXPECT_THROW({
        double val = p1[5];  
    }, out_of_range);
}


TEST(PolynomialTest, FunctionCall) {
    PolynomialOfOneVariable p1({1, 2, 3}); 

    double result = p1(2);  
    EXPECT_EQ(result, 17);
}

TEST(PolynomialTest, StreamOutput) {
    PolynomialOfOneVariable p1({1, 2, 3});  
    ostringstream out;
    out << p1;
    EXPECT_EQ(out.str(), "P(x)=3x^2+2x+1");
}