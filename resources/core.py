"""多资源池支付：按优先级扣费、上限钳制、整体回滚、幂等与回滚台账。

按 order 顺序扣费（order 里没有的池排在后面，同档次按池名升序）；
总额不足时整体回滚；set 钳制在 [0, cap]；req_id 幂等并记录台账供
refund 原样退还；spend 只扫描该玩家实际拥有的池，不随池子总数线性增长。
"""


class Pools:
    """玩家资源池台账。"""

    def __init__(self, order):
        self.order = list(order)
        self._rank = {name: index for index, name in enumerate(self.order)}
        self._amount = {}
        self._cap = {}
        self._pools = {}
        self.scanned = 0
        self._ledger = {}

    def set(self, player, pool, amount, cap):
        self._amount[(player, pool)] = min(cap, max(0, amount))
        self._cap[(player, pool)] = cap
        pools = self._pools.setdefault(player, [])
        if pool not in pools:
            pools.append(pool)
            pools.sort(key=self._priority)

    def get(self, player, pool):
        return self._amount.get((player, pool), 0)

    def _priority(self, pool):
        if pool in self._rank:
            return (0, self._rank[pool])
        return (1, pool)

    def _sorted_pools(self, player):
        return self._pools.get(player, ())

    def spend(self, player, cost, req_id):
        """按优先级扣费。"""
        record = self._ledger.get(req_id)
        if record is not None:
            return record["ok"]

        plan = []
        need = cost
        for pool in self._sorted_pools(player):
            value = self._amount[(player, pool)]
            if value <= 0:
                continue
            self.scanned += 1
            take = min(value, need)
            plan.append((pool, take))
            need -= take
            if need <= 0:
                break

        ok = need <= 0
        if ok:
            for pool, take in plan:
                self._amount[(player, pool)] -= take
        self._ledger[req_id] = {"player": player, "ok": ok,
                                "taken": plan if ok else [],
                                "refunded": False}
        return ok

    def refund(self, player, req_id):
        """回滚一次支付。"""
        record = self._ledger.get(req_id)
        if record is None or not record["ok"] or record["refunded"]:
            return False
        if record["player"] != player:
            return False
        for pool, take in record["taken"]:
            self._amount[(player, pool)] = (
                self._amount.get((player, pool), 0) + take)
        record["refunded"] = True
        return True

    def scanned_count(self):
        return self.scanned
