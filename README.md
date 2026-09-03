# Data Structures & Algorithms — through a finance lens

An ongoing collection of data structures and algorithms implemented from scratch in Python, each one applied to a real financial problem, because a stack is easier to remember when it's pricing a bond and a queue means more when it's running an order book.

**No dependencies** — everything is standard-library Python. Every file is self-checking: run it directly and it executes a demo with assertions.

```bash
python stacks/rpn_bond_pricer.py
python queues/order_book.py
```

## Contents

| Data structure | Applied to | File |
|---|---|---|
| **Stack** (LIFO) | A Reverse Polish Notation calculator that prices a fixed-coupon bond from its discounted-cash-flow expression, verified against the closed-form price | [`stacks/rpn_bond_pricer.py`](stacks/rpn_bond_pricer.py) |
| **Queue** (FIFO) | A limit order book with price-time priority matching: time priority within each price level, executions at the resting order's price, and a recorded trade tape | [`queues/order_book.py`](queues/order_book.py) |

*Growing as I go — next up: hash tables, graphs, and trees, each with a finance application.*

## Why this format

Each implementation follows the same pattern:

1. **The bare data structure first** — minimal, documented, no shortcuts borrowed from libraries
2. **A finance application built on it** — the structure doing actual work
3. **A self-verifying demo** — assertions that pin down correct behavior (a par bond must price at face value; an aggressive order must fill against the oldest resting order first)

Part of my broader quantitative finance portfolio — see my [profile](https://github.com/Ana-stesiia) for the pricing, volatility, and correlation projects.
