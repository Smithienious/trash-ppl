import unittest
from TestUtils import TestChecker
from AST import *

# !!! COMMENT THIS OUT
from main.d96.utils.AST import *


class CheckerSuite(unittest.TestCase):
    def test_bkel_1(self):
        input = Program(
            [
                ClassDecl(
                    Id("Program"), [
                        MethodDecl(Static(), Id("main"), [], Block([])),
                        AttributeDecl(
                            Instance(),
                            VarDecl(
                                Id("myVar"), StringType(),
                                StringLiteral("Hello World")
                            )
                        ),
                        AttributeDecl(
                            Instance(), VarDecl(Id("myVar"), IntType())
                        )
                    ]
                )
            ]
        )
        expect = """Redeclared Attribute: myVar"""
        self.assertTrue(TestChecker.test(input, expect, 1))

    def test_bkel_2(self):
        input = Program(
            [
                ClassDecl(
                    Id("Program"), [
                        MethodDecl(
                            Static(), Id("main"), [],
                            Block([Assign(Id("myVar"), IntLiteral(10))])
                        )
                    ]
                )
            ]
        )
        expect = """Undeclared Identifier: myVar"""
        self.assertTrue(TestChecker.test(input, expect, 2))

    def test_bkel_3(self):
        input = Program(
            [
                ClassDecl(
                    Id("Program"), [
                        MethodDecl(
                            Static(), Id("main"), [],
                            Block(
                                [
                                    ConstDecl(
                                        Id("myVar"), IntType(), IntLiteral(5)
                                    ),
                                    Assign(Id("myVar"), IntLiteral(10))
                                ]
                            )
                        )
                    ]
                )
            ]
        )
        expect = """Cannot Assign To Constant: AssignStmt(Id(myVar),IntLit(10))"""
        self.assertTrue(TestChecker.test(input, expect, 3))

    def test_bkel_4(self):
        input = Program(
            [
                ClassDecl(
                    Id("Program"),
                    [MethodDecl(Static(), Id("main"), [], Block([Break()]))]
                )
            ]
        )
        expect = """Break Not In Loop"""
        self.assertTrue(TestChecker.test(input, expect, 4))

    def test_bkel_5(self):
        input = Program(
            [
                ClassDecl(
                    Id("Program"), [
                        MethodDecl(
                            Static(), Id("main"), [],
                            Block(
                                [
                                    ConstDecl(
                                        Id("myVar"), IntType(),
                                        FloatLiteral(1.2)
                                    )
                                ]
                            )
                        )
                    ]
                )
            ]
        )
        expect = """Type Mismatch In Constant Declaration: ConstDecl(Id(myVar),IntType,FloatLit(1.2))"""
        self.assertTrue(TestChecker.test(input, expect, 5))

    # def test_undeclared_function(self):
    #     """Simple program: int main() {} """
    #     input = """int main() {foo();}"""
    #     expect = "Undeclared Function: foo"
    #     self.assertTrue(TestChecker.test(input, expect, 400))

    # def test_diff_numofparam_stmt(self):
    #     """More complex program"""
    #     input = """int main () {
    #         putIntLn();
    #     }"""
    #     expect = "Type Mismatch In Statement: CallExpr(Id(putIntLn),List())"
    #     self.assertTrue(TestChecker.test(input, expect, 401))

    # def test_diff_numofparam_expr(self):
    #     """More complex program"""
    #     input = """int main () {
    #         putIntLn(getInt(4));
    #     }"""
    #     expect = "Type Mismatch In Expression: CallExpr(Id(getInt),List(IntLiteral(4)))"
    #     self.assertTrue(TestChecker.test(input, expect, 402))

    # def test_undeclared_function_use_ast(self):
    #     """Simple program: int main() {} """
    #     input = Program(
    #         [
    #             FuncDecl(
    #                 Id("main"), [], IntType(),
    #                 Block([], [CallExpr(Id("foo"), [])])
    #             )
    #         ]
    #     )
    #     expect = "Undeclared Function: foo"
    #     self.assertTrue(TestChecker.test(input, expect, 403))

    # def test_diff_numofparam_expr_use_ast(self):
    #     """More complex program"""
    #     input = Program(
    #         [
    #             FuncDecl(
    #                 Id("main"), [], IntType(),
    #                 Block(
    #                     [], [
    #                         CallExpr(
    #                             Id("putIntLn"),
    #                             [CallExpr(Id("getInt"), [IntLiteral(4)])]
    #                         )
    #                     ]
    #                 )
    #             )
    #         ]
    #     )
    #     expect = "Type Mismatch In Expression: CallExpr(Id(getInt),List(IntLiteral(4)))"
    #     self.assertTrue(TestChecker.test(input, expect, 404))

    # def test_diff_numofparam_stmt_use_ast(self):
    #     """More complex program"""
    #     input = Program(
    #         [
    #             FuncDecl(
    #                 Id("main"), [], IntType(),
    #                 Block([], [CallExpr(Id("putIntLn"), [])])
    #             )
    #         ]
    #     )
    #     expect = "Type Mismatch In Statement: CallExpr(Id(putIntLn),List())"
    #     self.assertTrue(TestChecker.test(input, expect, 405))
