"""Bond pricing via a stack-based RPN calculator.

A LIFO stack powers a Reverse Polish Notation evaluator, which then
prices a fixed-coupon bond by building and evaluating the discounted
cash-flow expression in RPN. The result is verified against the
direct closed-form computation.

Data structure: stack (LIFO).
"""


class Stack:
    """A generic LIFO stack."""

    def __init__(self) -> None:
        self.items = []

    def push(self, item: float) -> None:
        """Push an item onto the top of the stack."""
        self.items.append(item)

    def pop(self) -> float:
        """Remove and return the top item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self.items.pop()

    def peek(self) -> float:
        """Return the top item without removing it. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.items[-1]

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def __len__(self) -> int:
        return len(self.items)


class RPNCalculator:
    """Evaluates arithmetic expressions in Reverse Polish Notation."""

    OPERATORS = {"+", "-", "*", "/", "**"}

    def evaluate(self, expression: str) -> float:
        """Evaluate an RPN expression string and return the result.

        A fresh stack is used per call, so a failed evaluation can
        never leak state into the next one.
        """
        stack = Stack()

        for token in expression.split():
            if token not in self.OPERATORS:
                try:
                    stack.push(float(token))
                except ValueError:
                    raise ValueError(f"unknown token '{token}'")
                continue

            try:
                b = stack.pop()
                a = stack.pop()
            except IndexError:
                raise ValueError(f"not enough operands for operator '{token}'")

            if token == "+":
                result = a + b
            elif token == "-":
                result = a - b
            elif token == "*":
                result = a * b
            elif token == "**":
                result = a ** b
            else:  # "/"
                if b == 0:
                    raise ValueError("division by zero")
                result = a / b

            stack.push(result)

        if len(stack) != 1:
            raise ValueError("too many operands in expression")
        return stack.pop()


class BondPricingExpression:
    """Prices a fixed-coupon bond by building and evaluating its
    discounted-cash-flow expression in RPN."""

    def __init__(self, face_value: float, coupon_rate: float,
                 yield_rate: float, periods: int) -> None:
        if periods < 1:
            raise ValueError("periods must be at least 1")
        self.face_value = face_value
        self.coupon_rate = coupon_rate
        self.yield_rate = yield_rate
        self.periods = periods
        self.calculator = RPNCalculator()

    def price_direct(self) -> float:
        """Bond price computed directly — used to verify the RPN route."""
        coupon = self.face_value * self.coupon_rate
        price = sum(coupon / (1 + self.yield_rate) ** t
                    for t in range(1, self.periods + 1))
        price += self.face_value / (1 + self.yield_rate) ** self.periods
        return price

    def build_rpn(self) -> str:
        """Build the RPN expression for the bond price.

        Each cash flow C / (1+y)^t becomes 'C base t ** /', with '+'
        folding the running sum after every term beyond the first.
        """
        coupon = self.face_value * self.coupon_rate
        base = 1 + self.yield_rate
        tokens = []

        for t in range(1, self.periods + 1):
            tokens.extend([str(coupon), str(base), str(t), "**", "/"])
            if t > 1:
                tokens.append("+")

        tokens.extend([str(self.face_value), str(base),
                       str(self.periods), "**", "/", "+"])
        return " ".join(tokens)

    def price(self) -> float:
        """Bond price via the RPN evaluator."""
        return self.calculator.evaluate(self.build_rpn())


if __name__ == "__main__":
    # A bond priced at par (coupon = yield) must come out at face value,
    # and the RPN route must agree with the direct formula.
    bond = BondPricingExpression(face_value=1000, coupon_rate=0.05,
                                 yield_rate=0.05, periods=3)
    print("RPN expression:", bond.build_rpn())
    rpn_price, direct_price = bond.price(), bond.price_direct()
    print(f"RPN price:    {rpn_price:.6f}")
    print(f"Direct price: {direct_price:.6f}")
    assert abs(rpn_price - direct_price) < 1e-9
    assert abs(rpn_price - 1000.0) < 1e-9      # par bond sanity check

    # A discount bond (yield above coupon) must price below par
    discount = BondPricingExpression(1000, 0.03, 0.06, periods=5)
    assert discount.price() < 1000
    print(f"Discount bond: {discount.price():.2f} (below par, as expected)")
    print("all checks passed")
