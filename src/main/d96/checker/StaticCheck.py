"""
 * @author nhphung
"""
from AST import *
# Have to import Visitor because CodeGenerator does not import by itself
# What the fuck is this chain of responsibility?
from Visitor import *
from StaticError import *

# !!! COMMENT THIS OUT
from main.d96.utils.AST import *


class MetaAttribute:
    def __init__(
        self,
        name: str,
        type: Type,
        static: bool = False,
        constant: bool = False
    ):
        self.name = name
        self.type = type
        self.static = static
        self.constant = constant


class MetaVariable:
    def __init__(
        self, name: str, type: Type, scope: int, constant: bool = False
    ):
        self.name = name
        self.type = type
        self.scope = scope
        self.constant = constant


class MetaMethod:
    def __init__(
        self,
        name: str,
        partype: List[VarDecl],
        rettype: Type = None,
        static: bool = False
    ):
        self.name = name
        self.partype = partype
        self.rettype = rettype
        self.static = static

        # { str: List[MetaVariable] }
        # because we must keep track of variables in outer scope
        self.variable = dict()

        # Not in loop
        self.loop = 0

        # Already in scope of class
        self.scope = 1

    def enter_loop(self):
        self.loop += 1

    def exit_loop(self):
        self.loop -= 1

    def enter_scope(self):
        self.scope += 1

    def exit_scope(self):
        self.scope -= 1
        # Remove inner scope variables
        for name, val in self.variable.items():
            if val[-1].scope > self.scope:
                self.variable[name].pop()

    def add_var(self, name: str, type: Type):
        self.check_redeclared_variable(name)
        if name in self.variable.keys():
            self.variable[name] += [MetaVariable(name, type, self.scope)]
        else:
            self.variable[name] = [MetaVariable(name, type, self.scope)]

    def add_const(self, name: str, type: Type):
        self.check_redeclared_variable(name)
        if name in self.variable.keys():
            self.variable[name] += [MetaVariable(name, type, self.scope, True)]
        else:
            self.variable[name] = [MetaVariable(name, type, self.scope, True)]

    def check_entrypoint(self):
        return self.name == "main" and self.static

    def check_redeclared_variable(self, name: str):
        if name in self.variable.keys():
            raise Redeclared(Variable(), name)


class MetaClass:
    # PEP 484: Forward reference
    def __init__(self, name: str, super_cls: 'MetaClass' = None):
        self.name = name
        self.attr = dict()
        self.method = dict()
        if super_cls:
            self.attr = super_cls.attr.copy()
            self.method = super_cls.method.copy()

    def add_attr(
        self,
        name: str,
        type: Type,
        static: bool = False,
        constant: bool = False
    ):
        self.check_redeclared_attr(name)
        self.attr[name] = MetaAttribute(name, type, static, constant)

    def add_method(
        self,
        name: str,
        partype: List[VarDecl],
        rettype: Type = None,
        static: bool = False
    ):
        self.check_redeclared_method(name, partype)
        if self.name == "Program" and name == "main":
            static = True
        self.method[name] = MetaMethod(name, partype, rettype, static)

    def get_or_raise_undeclared_attr(self, name: str):
        if name not in self.attr.keys():
            raise Undeclared(Attribute(), name)
        return self.attr[name]

    def get_or_raise_undeclared_method(self, name: str):
        if name not in self.method.keys():
            raise Undeclared(Method(), name)
        return self.method[name]

    def check_entrypoint(self):
        return any(
            [method.check_entrypoint()
             for method in self.method.values()] if self.method else [False]
        )

    def check_redeclared_attr(self, name: str):
        if name in self.attr.keys():
            raise Redeclared(Attribute(), name)

    def check_redeclared_method(self, name: str, partype: List[VarDecl]):
        if name in self.method.keys():
            # Test with type of parameters, not names
            partype_old = list(
                map(lambda x: type(x.varType), self.method[name].partype)
            )
            partype_new = list(map(lambda x: type(x.varType), partype))
            if partype_old == partype_new:
                raise Redeclared(Method(), name)


class MetaProgram:
    def __init__(self):
        self.cls = dict()

    def add_class(self, name: str, super_cls=None):
        self.check_redeclared_class(name)
        if super_cls:
            self.check_undeclared_class(super_cls)
        self.cls[name] = MetaClass(
            name, self.cls[super_cls] if super_cls else None
        )

    def add_method(self, cls: str, name: str, partype: List[VarDecl], rettype:Type=None, static:bool=False):
        self.check_undeclared_class(cls)
        self.cls[cls].add_method(name, partype, rettype, static)

    def add_attr(self, cls:str, name:str, type:Type, static:bool=False, constant:bool=False):
        self.check_undeclared_class(cls)
        self.cls[cls].add_attr(name, type, static, constant)

    def get_class(self, name: str):
        self.check_undeclared_class(name)
        return self.cls[name]

    def check_entrypoint(self):
        return any(
            [cls.check_entrypoint()
             for cls in self.cls.values()] if self.cls else [False]
        )

    def check_redeclared_class(self, name: str):
        if name in self.cls.keys():
            raise Redeclared(Class(), name)

    def check_undeclared_class(self, name: str):
        if name not in self.cls.keys():
            raise Undeclared(Class(), name)


class StaticChecker:
    # c: Tuple[MetaClass, MetaProgram]

    def __init__(self, ast):
        self.ast = ast

    # Copy from BaseVisitor because it doesn't do shit
    def visit(self, ast, param):
        return ast.accept(self, param)

    # Copy from Utils because BKeL does not have this file
    def lookup(self, name, lst, func):
        for x in lst:
            if name == func(x):
                return x
        return None

    def check(self):
        return self.visit(self.ast, None)

    def visitProgram(self, ast, c=None):
        self.meta_program = MetaProgram()

        # Traverse all classes
        [self.visit(x, c) for x in ast.decl]

        if not self.meta_program.check_entrypoint():
            raise NoEntryPoint()

    def visitClassDecl(self, ast, c=None):
        # Load classes into meta_program
        self.meta_program.add_class(
            ast.classname.name, ast.parentname.name if ast.parentname else None
        )

        # Make classes load attributes and methods
        [
            self.visit(x, self.meta_program.get_class(ast.classname.name))
            for x in ast.memlist
        ]

    def visitAttributeDecl(self, ast, c: MetaClass):
        static = type(ast.kind) is Static
        const = type(ast.decl) is ConstDecl
        if const:
            partype = ast.decl.constType
            name = ast.decl.constant.name
        else:
            partype = ast.decl.varType
            name = ast.decl.variable.name
        c.add_attr(name, partype, static, const)

    def visitMethodDecl(self, ast, meta_cls: MetaClass):
        static = type(ast.kind) is Static
        meta_cls.add_method(ast.name.name, ast.param, None, static)
        [
            self.visit(
                ast.body, (
                    meta_cls,
                    meta_cls.get_or_raise_undeclared_method(ast.name.name)
                )
            )
        ]

    def visitBlock(self, ast, c: tuple):
        meta_class, meta_method = c
        meta_method.enter_scope()
        [self.visit(x, c) for x in ast.inst]
        meta_method.exit_scope()

    def visitVarDecl(self, ast, c: tuple):
        meta_class, meta_method = c
        meta_method.add_var(ast.variable.name, ast.varType)
        # Var can exist without being initialized
        if ast.varInit:
            rettype = self.visit(ast.varInit, c)
            if type(rettype) != type(ast.varType):
                raise TypeMismatchInStatement(ast)

    def visitConstDecl(self, ast, c: tuple):
        meta_class, meta_method = c
        meta_method.add_const(ast.constant.name, ast.constType)
        if not ast.value:
            raise IllegalConstantExpression(ast.value)
        rettype = self.visit(ast.value, c)
        if type(rettype) != type(ast.constType):
            raise TypeMismatchInConstant(ast)

    def visitAssign(self, ast, c):
        lhs = self.visit(ast.lhs, c)
        rhs = self.visit(ast.exp, c)

        if not lhs:
            raise Undeclared(Identifier(), ast.lhs.name)

        lhs = lhs[-1]
        if lhs.constant:
            raise CannotAssignToConstant(ast)

        # TODO Cannot mismatch type

    # LHS of Assign
    def visitId(self, ast, c: tuple):
        meta_class, meta_method = c
        if ast.name not in meta_method.variable.keys():
            raise Undeclared(Identifier(), ast.name)
        return meta_method.variable[ast.name]

    def visitCallStmt(self, ast, c: tuple):
        cls = self.meta_program.get_class(ast.obj.name)
        method = cls.get_or_raise_undeclared_method(ast.method.name)
        partype = [self.visit(x, c) for x in ast.param]

        # We don't care about rettype of statements
        # Else it would be expressions
        if method.partype != partype:
            raise TypeMismatchInStatement(ast)

    def visitCallExpr(self, ast, c: tuple):
        cls = self.meta_program.get_class(ast.obj.name)
        method = cls.get_or_raise_undeclared_method(ast.method.name)
        partype = [self.visit(x, c) for x in ast.param]

        # Expression must return type
        if not method.rettype or method.partype != partype:
            raise TypeMismatchInExpression(ast)

        return method.rettype

    def visitIf(self, ast, c: tuple):
        condition = self.visit(ast.expr, c)
        # TODO concatenate condition
        if type(condition) != BoolType:
            raise TypeMismatchInStatement(ast)
        self.visit(ast.thenStmt, c)
        self.visit(ast.elseStmt, c)

    def visitFor(self, ast, c):
        pass

    def visitBreak(self, ast, c):
        meta_class, meta_method = c
        if meta_method.loop < 1:
            raise MustInLoop(Break())

    def visitContinue(self, ast, c):
        meta_class, meta_method = c
        if meta_method.loop < 1:
            raise MustInLoop(Continue())

    def visitReturn(self, ast, c):
        meta_class, meta_method = c
        meta_method.rettype = self.visit(ast.expr, c)

    def visitFieldAccess(self, ast, c: tuple):
        # meta_class, meta_method = c
        cls = self.meta_program.get_class(ast.obj.name)
        attr = cls.get_or_raise_undeclared_attr(ast.fieldname.name)
        return attr.type

    def visitBinaryOp(self, ast, c: BinaryOp):
        left = self.visit(ast.left, c)
        right = self.visit(ast.right, c)
        op = ast.op

        # Arithmetic
        if op == '%':
            if type(left) is not IntLiteral or type(right) is not IntLiteral:
                raise TypeMismatchInExpression(ast)
        if op in ['+', '-', '*', '/']:
            if type(left) not in [
                IntLiteral, FloatLiteral
            ] or type(right) not in [IntLiteral, FloatLiteral]:
                raise TypeMismatchInExpression(ast)
            if type(left) is IntLiteral and type(right) is IntLiteral:
                return IntType()
            return FloatType()

        # Boolean
        if op == '==.':
            if type(left
                   ) is not StringLiteral or type(right) is not StringLiteral:
                raise TypeMismatchInExpression(ast)
            return BoolType()
        if op in ['&&', '||']:
            if type(left) is not BooleanLiteral or type(
                right
            ) is not BooleanLiteral:
                raise TypeMismatchInExpression(ast)
            return BoolType()

        # String
        if op == '+.':
            if type(left
                   ) is not StringLiteral or type(right) is not StringLiteral:
                raise TypeMismatchInExpression(ast)
            return StringType()

        # Relational
        if op in ['==', '!=']:
            if type(left) not in [
                IntLiteral, BooleanLiteral
            ] or type(right) not in [IntLiteral, BooleanLiteral]:
                raise TypeMismatchInExpression(ast)
            return BoolType()
        if op in ['<', '>', '<=', '>=']:
            if type(left) not in [
                IntLiteral, FloatLiteral
            ] or type(right) not in [IntLiteral, FloatLiteral]:
                raise TypeMismatchInExpression(ast)
            return BoolType()

    def visitUnaryOp(self, ast, c: UnaryOp):
        body = ast.body
        op = ast.op

        # Arithmetic
        if op == '-':
            if type(body) not in [IntLiteral, FloatLiteral]:
                raise TypeMismatchInExpression(ast)
            return IntType() if type(body) is IntLiteral else FloatType()

        # Boolean
        if op == '!':
            if type(body) is not BooleanLiteral:
                raise TypeMismatchInExpression(ast)
            return BoolType()

    def visitIntLiteral(self, ast, c):
        return IntType()

    def visitFloatLiteral(self, ast, c):
        return FloatType()

    def visitBooleanLiteral(self, ast, c):
        return BoolType()
