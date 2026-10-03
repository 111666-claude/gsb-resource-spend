"""多资源池支付：按优先级扣费、上限钳制、整体回滚、幂等与回滚台账。

缺陷：不按优先级顺序扣、不足时不回滚（能扣多少扣多少）、set 不钳制上限、
同一个 req_id 重复结算、refund 不退资源、每次支付扫描全部资源池。
"""


class Pools:
    """玩家资源池台账。"""

    def __init__(self, order):
        self.order = list(order)
        self.amount = {}
        self.cap = {}
        self.memo = {}
        self.spent = {}
        self.scanned = 0

    def set(self, player, pool, amount, cap):
        self.amount[(player, pool)] = amount
        self.cap[(player, pool)] = cap

    def get(self, player, pool):
        return self.amount.get((player, pool), 0)

    def spend(self, player, cost, req_id):
        """按优先级扣费。"""
        self.scanned += len(self.amount)
        need = cost
        used = []
        for (owner, pool), value in self.amount.items():
            if owner != player:
                continue
            take = min(value, need)
            self.amount[(owner, pool)] = value - take
            used.append((pool, take))
            need -= take
            if need == 0:
                break
        self.memo[req_id] = True
        self.spent[req_id] = used
        return True

    def refund(self, player, req_id):
        """回滚一次支付。"""
        return True

    def scanned_count(self):
        return self.scanned
