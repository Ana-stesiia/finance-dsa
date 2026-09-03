"""Limit order book with price-time priority matching.

A FIFO queue implements time priority within each price level, and a
matching engine crosses the book whenever the best bid meets the best
ask, executing at the resting order's price and recording every trade.

Data structure: queue (FIFO).

Note: this module is deliberately NOT named ``queue.py`` — that would
shadow Python's standard-library ``queue`` module and break any import
of it elsewhere on the path.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


class Queue:
    """A generic FIFO queue."""

    def __init__(self) -> None:
        self._items = deque()

    def enqueue(self, item) -> None:
        """Add an item to the back of the queue."""
        self._items.append(item)

    def dequeue(self):
        """Remove and return the front item. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self._items.popleft()

    def peek(self):
        """Return the front item without removing it. Raises IndexError if empty."""
        if self.is_empty():
            raise IndexError("peek from empty queue")
        return self._items[0]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


@dataclass
class Order:
    order_id: str
    side: str        # "bid" or "ask"
    price: float
    quantity: float
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.side not in ("bid", "ask"):
            raise ValueError(f"side must be 'bid' or 'ask', got '{self.side}'")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")


@dataclass(frozen=True)
class Trade:
    """A single execution on the tape."""
    bid_id: str
    ask_id: str
    price: float
    quantity: float


class PriceLevel:
    """All resting orders at one price, in time priority."""

    def __init__(self, price: float) -> None:
        self.price = price
        self.orders = Queue()

    def add_order(self, order: Order) -> None:
        self.orders.enqueue(order)

    def next_order(self) -> Order:
        """Peek at the front order without removing it."""
        return self.orders.peek()

    def fill_order(self) -> Order:
        """Remove and return the front order (fully executed)."""
        return self.orders.dequeue()

    def is_empty(self) -> bool:
        return self.orders.is_empty()

    @property
    def total_quantity(self) -> float:
        return sum(order.quantity for order in self.orders)

    def __len__(self) -> int:
        return len(self.orders)


class OrderBook:
    """A limit order book with price-time priority matching."""

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.bids: dict[float, PriceLevel] = {}
        self.asks: dict[float, PriceLevel] = {}
        self.trades: list[Trade] = []       # the tape

    def add_order(self, order: Order) -> list[Trade]:
        """Add an order to the book, match, and return trades executed."""
        book_side = self.bids if order.side == "bid" else self.asks
        if order.price not in book_side:
            book_side[order.price] = PriceLevel(order.price)
        book_side[order.price].add_order(order)
        return self.match_orders()

    def best_bid(self) -> float | None:
        """Highest bid price, or None if no bids."""
        return max(self.bids) if self.bids else None

    def best_ask(self) -> float | None:
        """Lowest ask price, or None if no asks."""
        return min(self.asks) if self.asks else None

    def match_orders(self) -> list[Trade]:
        """Cross the book while it is crossed; return the executed trades.

        Executions happen at the RESTING order's price — the order that
        was in the book first (earlier timestamp) sets the price, and
        the incoming order receives the price improvement.
        """
        executed = []
        while self.bids and self.asks and self.best_bid() >= self.best_ask():
            bid_level = self.bids[self.best_bid()]
            ask_level = self.asks[self.best_ask()]
            bid_order = bid_level.next_order()
            ask_order = ask_level.next_order()

            trade_qty = min(bid_order.quantity, ask_order.quantity)
            trade_price = (bid_order.price
                           if bid_order.timestamp <= ask_order.timestamp
                           else ask_order.price)

            trade = Trade(bid_order.order_id, ask_order.order_id,
                          trade_price, trade_qty)
            executed.append(trade)
            self.trades.append(trade)

            bid_order.quantity -= trade_qty
            ask_order.quantity -= trade_qty
            if bid_order.quantity == 0:
                bid_level.fill_order()
            if ask_order.quantity == 0:
                ask_level.fill_order()
            if bid_level.is_empty():
                del self.bids[bid_level.price]
            if ask_level.is_empty():
                del self.asks[ask_level.price]
        return executed

    def __repr__(self) -> str:
        lines = [f"OrderBook({self.ticker})", "  ASKS"]
        for price in sorted(self.asks, reverse=True):
            level = self.asks[price]
            lines.append(f"    {price:.2f}  [{len(level)} orders, "
                         f"{level.total_quantity:g} qty]")
        lines.append("  ---")
        lines.append("  BIDS")
        for price in sorted(self.bids, reverse=True):
            level = self.bids[price]
            lines.append(f"    {price:.2f}  [{len(level)} orders, "
                         f"{level.total_quantity:g} qty]")
        return "\n".join(lines)


if __name__ == "__main__":
    book = OrderBook("AAPL")
    book.add_order(Order("001", "bid", 100.00, 500))
    book.add_order(Order("002", "bid", 100.00, 300))
    book.add_order(Order("003", "bid", 99.50, 200))
    book.add_order(Order("004", "ask", 101.00, 400))
    book.add_order(Order("005", "ask", 100.50, 100))

    print(book)
    assert book.best_bid() == 100.00 and book.best_ask() == 100.50

    # An aggressive ask at 99.50 crosses the 100.00 bids:
    # price-time priority says order 001 (earlier at 100.00) fills first,
    # at the resting bid's price of 100.00.
    trades = book.add_order(Order("006", "ask", 99.50, 400))
    print("\ntrades executed:")
    for t in trades:
        print(f"  {t.quantity:g} @ {t.price:.2f}  "
              f"(bid {t.bid_id} x ask {t.ask_id})")
    print()
    print(book)

    assert trades == [Trade("001", "006", 100.00, 400)]
    assert book.bids[100.00].next_order().order_id == "001"   # partially left
    assert book.bids[100.00].next_order().quantity == 100
    print("\nall checks passed")
