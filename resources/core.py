"""多资源池支付：按优先级扣费、上限钳制、整体回滚、幂等与回滚台账。"""


class Pools:
    """玩家资源池台账。"""

    def __init__(self, order):
        self.order = list(order)
        self.rank = {pool: index for index, pool in enumerate(self.order)}
        self.amount = {}
        self.cap = {}
        self.memo = {}
        self.spent = {}
        self.scanned = 0

    def set(self, player, pool, amount, cap):
        self.cap[(player, pool)] = cap
        self.amount.setdefault(player, {})[pool] = min(max(amount, 0), cap)

    def get(self, player, pool):
        return self.amount.get(player, {}).get(pool, 0)

    def priority(self, player):
        pools = self.amount.get(player, {})
        size = len(self.rank)
        return sorted(pools, key=lambda pool: (self.rank.get(pool, size), pool))

    def spend(self, player, cost, req_id):
        """按优先级扣费；不足时整体回滚，同一 req_id 只结算一次。"""
        key = (player, req_id)
        if key in self.memo:
            return self.memo[key]
        pools = self.amount.get(player, {})
        sequence = self.priority(player)
        self.scanned += len(sequence)
        total = 0
        for pool in sequence:
            total += pools[pool]
        if total < cost:
            self.memo[key] = False
            return False
        need = cost
        used = []
        for pool in sequence:
            if need <= 0:
                break
            self.scanned += 1
            take = min(pools[pool], need)
            if take > 0:
                pools[pool] -= take
                used.append((pool, take))
                need -= take
        self.memo[key] = True
        self.spent[key] = used
        return True

    def refund(self, player, req_id):
        """回滚一次支付：原样退还，只退一次，未知 req 返回 False。"""
        key = (player, req_id)
        used = self.spent.pop(key, None)
        if used is None:
            return False
        pools = self.amount.setdefault(player, {})
        for pool, take in used:
            pools[pool] = pools.get(pool, 0) + take
        return True

    def scanned_count(self):
        return self.scanned
