import re
import os
from enum import Enum
import random
from dotenv import load_dotenv

load_dotenv()


class Error:
    def __init__(self, error_name, details):
        self.error_name = error_name
        self.details = details

    def __str__(self):
        return f"EXCEPTION! -- {self.error_name}: {self.details}"


class IllegalCharError(Error):
    def __init__(self, details):
        super().__init__("Illegal Character", details)


class InvalidSyntaxError(Error):
    def __init__(self, details):
        super().__init__("Invalid Syntax", details)


class TokenType(Enum):
    TT_STR = "TT_STR"
    TT_INT = "TT_INT"
    TT_FLOAT = "TT_FLOAT"
    TT_EOF = "TT_EOF"
    TT_KEYWORD = "TT_KEYWORD"


WHITESPACE = " \t\n\r"
LETTER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGIT = "0123456789"
DECIMAL_POINT = "."
KEYWORDS = [
    "DEPOSIT",
    "WITHDRAW",
    "BALANCE",
    "CREATE",
    "FIRSTNAME",
    "LASTNAME",
    "ACCOUNT",
]
ACCOUNT_NUMBER_FORMAT = "^[A-Z]{2}[0-9]{6}"


class Token:
    def __init__(self, type: TokenType, value: any):
        self.type: TokenType = type
        self.value = value

    def __str__(self):
        return f"Token({self.type.value}, '{self.value}')"

    def __repr__(self):
        return self.__str__()


class Lexer:
    def __init__(self, source):
        self.source = source
        self.current_char = None
        self.index = -1
        self.tokens = []

    def advance(self):
        self.index += 1
        if self.index < len(self.source):
            self.current_char = self.source[self.index]
        else:
            self.current_char = None

    def lex(self) -> tuple[list[Token], Error]:
        self.advance()
        while self.index < len(self.source):
            if self.current_char in WHITESPACE:
                self.advance()
            elif self.current_char in LETTER:
                self.tokens.append(self.lex_word())
            elif self.current_char in DIGIT:
                self.tokens.append(self.lex_number())
            else:
                return [], IllegalCharError(self.current_char)
            self.advance()

        # self.tokens.append(Token(TokenType.TT_EOF, None))
        return self.tokens, None

    def lex_word(self):
        word = ""
        while self.current_char is not None and self.current_char not in WHITESPACE:
            word += self.current_char
            self.advance()
        if word in KEYWORDS:
            return Token(TokenType.TT_KEYWORD, word)
        return Token(TokenType.TT_STR, word)

    def lex_number(self):
        number = ""
        while self.current_char is not None and (
            self.current_char in DIGIT or self.current_char == "."
        ):
            number += self.current_char
            self.advance()
        if "." in number:
            return Token(TokenType.TT_FLOAT, float(number))
        else:
            return Token(TokenType.TT_INT, int(number))


class Node:
    pass


class CreateNode(Node):
    def __init__(
        self,
        firstname,
        lastname,
        balance=Token(TokenType.TT_INT, 0),
        account_identifier=None,
    ):
        self.firstname = firstname
        self.lastname = lastname
        self.account_identifier = account_identifier
        if not account_identifier:
            self.account_identifier = self.build_account_identifier()
        self.balance = balance

    def build_account_identifier(self):
        # First letter of the first name and first letter of the last name and 6 random digits
        return Token(
            TokenType.TT_STR,
            self.firstname.value[0]
            + self.lastname.value[0]
            + str(random.randint(100000, 999999)),
        )

    def __repr__(self):
        return (
            f"CreateNode({self.firstname}, {self.lastname}, {self.account_identifier})"
        )


class DepositNode(Node):
    def __init__(self, account_identifier, amount):
        self.account_identifier = account_identifier
        self.amount = amount

    def __repr__(self):
        return f"DepositNode({self.account_identifier}, {self.amount})"


class WithdrawNode(Node):
    def __init__(self, account_identifier, amount):
        self.account_identifier = account_identifier
        self.amount = amount

    def __repr__(self):
        return f"WithdrawNode({self.account_identifier}, {self.amount})"


class BalanceNode(Node):
    def __init__(self, account_identifier):
        self.account_identifier = account_identifier

    def __repr__(self):
        return f"BalanceNode({self.account_identifier})"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.index = -1

    def advance(self):
        self.index += 1
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
        else:
            self.current_token = None

    def parse(self):
        statements = []
        self.advance()
        while self.current_token is not None:
            statement = self.parse_statement()
            if type(statement) == InvalidSyntaxError:
                return [], statement
            statements.append(statement)
            self.advance()
        return statements, None

    def parse_statement(self):
        if self.current_token.type == TokenType.TT_KEYWORD:
            if self.current_token.value == "CREATE":
                return self.parse_create()
            elif self.current_token.value == "DEPOSIT":
                return self.parse_deposit()
            elif self.current_token.value == "WITHDRAW":
                return self.parse_withdraw()
            elif self.current_token.value == "BALANCE":
                return self.parse_balance()
        return InvalidSyntaxError(
            "Expected keyword CREATE, DEPOSIT, WITHDRAW, or BALANCE"
        )

    def parse_deposit(self):
        self.advance()
        if self.current_token is None or self.current_token.type != TokenType.TT_STR:
            return InvalidSyntaxError("Expected a string")
        account_identifier = self.current_token

        self.advance()
        if self.current_token is None and (
            self.current_token.type != TokenType.TT_FLOAT
            or self.current_token.type != TokenType.TT_INT
        ):
            return InvalidSyntaxError("Expected a number")
        amount = self.current_token
        return DepositNode(account_identifier, amount)

    def parse_withdraw(self):
        self.advance()
        if self.current_token is None or self.current_token.type != TokenType.TT_STR:
            return InvalidSyntaxError("Expected a string")
        account_identifier = self.current_token

        self.advance()
        if self.current_token is None and (
            self.current_token.type != TokenType.TT_FLOAT
            or self.current_token.type != TokenType.TT_INT
        ):
            return InvalidSyntaxError("Expected a number")
        amount = self.current_token
        return WithdrawNode(account_identifier, amount)

    def parse_balance(self):
        self.advance()
        if self.current_token.type == TokenType.TT_STR:
            account_identifier = self.current_token
        else:
            return InvalidSyntaxError("Expected a string")
        return BalanceNode(account_identifier)

    def parse_create(self):
        # Check if the next token is the keyword FIRSTNAME
        self.advance()
        if self.current_token is None or (
            self.current_token.type != TokenType.TT_KEYWORD
            and self.current_token.value != "FIRSTNAME"
        ):
            return InvalidSyntaxError("Expected keyword FIRSTNAME")
        self.advance()

        # Check if the next token is a string, this will represent the first name
        if self.current_token is None and self.current_token.type == TokenType.TT_STR:
            return InvalidSyntaxError("Expected a string")
        first_name = self.current_token
        self.advance()

        # Check if the next token is the keyword LASTNAME
        if self.current_token is None or (
            self.current_token.type != TokenType.TT_KEYWORD
            and self.current_token.value != "LASTNAME"
        ):
            return InvalidSyntaxError("Expected the keyword LASTNAME")
        self.advance()

        # Check if the next token is a string, this will represent the last name
        if self.current_token is None and self.current_token.type == TokenType.TT_STR:
            return InvalidSyntaxError("Expected a string")
        last_name = self.current_token

        # Check for optional keywords BALANCE and ACCOUNT
        balance = Token(TokenType.TT_INT, 0)
        account_identifier = None

        self.advance()
        while self.current_token is not None:
            if self.current_token.type == TokenType.TT_KEYWORD:
                # Should be either BALANCE or ACCOUNT
                if self.current_token.value == "BALANCE":
                    # Check if the next token is a number, return SyntaxError if not
                    self.advance()
                    if (
                        self.current_token.type == TokenType.TT_INT
                        or self.current_token.type == TokenType.TT_FLOAT
                    ):
                        balance = self.current_token
                    else:
                        return InvalidSyntaxError("Expected a number")
                elif self.current_token.value == "ACCOUNT":
                    # Check if the next token is a string, return SyntaxError if not
                    self.advance()
                    if self.current_token.type == TokenType.TT_STR:
                        # Check if the account number is in the correct format
                        if re.match(ACCOUNT_NUMBER_FORMAT, self.current_token.value):
                            account_identifier = self.current_token
                        else:
                            return InvalidSyntaxError("Invalid account number format")
                    else:
                        return InvalidSyntaxError("Expected a string")

            self.advance()

        return CreateNode(first_name, last_name, balance, account_identifier)


class AccountTable:
    def __init__(self):
        self.accounts = {}

    def add_account(self, account):
        result = self.get_account(account.account_identifier.value)
        if not result:
            self.accounts[account.account_identifier.value] = account
            return account

        print("Account already exists... picking a new account number")

    def get_account(self, account_identifier):
        if account_identifier in self.accounts:
            return self.accounts[account_identifier]
        else:
            return None


class Interpreter:
    def __init__(self, account_table):
        self.account_table = account_table

    def interpret(self, statements):
        for statement in statements:
            self.visit(statement)

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name)
        return method(node)

    def visit_CreateNode(self, node):
        self.account_table.add_account(node)
        print("Account created: ", node.account_identifier.value)
        return node

    def visit_DepositNode(self, node: DepositNode):
        account = self.account_table.get_account(node.account_identifier.value)
        if account:
            account.balance.value += node.amount.value
            print(f"Deposit of ${node.amount.value} into account {node.account_identifier.value} successful")
        else:
            print("Account not found")
        return node

    def visit_WithdrawNode(self, node: WithdrawNode):
        account = self.account_table.get_account(node.account_identifier.value)
        if account:
            if account.balance.value < node.amount.value:
                print(f"Insufficient funds in account {node.account_identifier.value}")
            else:
                account.balance.value -= node.amount.value
                print(f"Withdrawal of ${node.amount.value} from account {node.account_identifier.value} successful")
        else:
            print("Account not found")
        return node

    def visit_BalanceNode(self, node):
        account = self.account_table.get_account(node.account_identifier.value)
        if account:
            print(f"Balance for account {node.account_identifier.value}: ${account.balance.value}")
        else:
            print("Account not found")

        return node


global_account_table = AccountTable()


def run(stream):

    lexer = Lexer(stream)
    tokens, error = lexer.lex()
    if error:
        return error
    if os.getenv("DEBUG") == "1":
        print(tokens)

    parser = Parser(tokens)
    ast, error = parser.parse()
    if error:
        return error
    if os.getenv("DEBUG") == "1":
        print(ast)

    interpreter = Interpreter(global_account_table)
    interpreter.interpret(ast)
    return None
