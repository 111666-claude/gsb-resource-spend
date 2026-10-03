# resource-spend

多资源池支付：按优先级扣费、上限钳制、整体回滚、幂等与回滚台账，
只用 Python 标准库。

```
python3 -m resources.cli --sample order
python3 -m resources.cli --sample rollback
python3 -m resources.cli --sample cap
python3 -m resources.cli --sample dup
python3 -m resources.cli --sample refund
python3 -m resources.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **上限**：`set` 把数量钳制在 `[0, cap]`。
- **优先级**：`spend` 按 `order` 里的顺序扣，`order` 里没有的池排在后面，
  同档次按池名升序。
- **整体回滚**：所有池加起来不够 `cost` 时 `spend` 返回 False，
  且任何一个池的数量都不许改变。
- **守恒**：成功的支付让总量恰好减少 `cost`。
- **幂等**：同一个 `req_id` 只结算一次，重复 `spend` 返回上次结果且不再扣。
- **回滚台账**：`refund` 把该 `req_id` 扣掉的量原样还回去，只能回滚一次；
  未知 `req_id` 返回 False。
- **不变量**：任何池的数量都不超过上限也不为负；同一串支付与回滚序列
  重复执行结果相同。
- **查询代价**：`spend` 不许扫描全部资源池，`scanned_count`
  不随池子总数线性增长。
- **规模**：10 万个池、每秒 10 万次支付，单次摊还 O(实际用到的池数)。

## 输出契约（不改格式）

```
ok=.. rage=.. mana=..
rage=..
scanned=..
```

## 目录

```
resources/core.py   顺序、回滚、幂等与台账
resources/cli.py    命令行入口
tests/              unittest 用例
```
