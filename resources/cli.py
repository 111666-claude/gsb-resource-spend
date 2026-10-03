"""命令行入口：跑资源支付样例。"""

import argparse

from .core import Pools


def build_parser():
    parser = argparse.ArgumentParser(prog="resource-spend", description="多资源池支付")
    parser.add_argument("--sample", default="order",
                        help="order / rollback / cap / dup / refund / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "order":
        world = Pools(order=("rage", "mana"))
        world.set("p1", "mana", 1, 100)
        world.set("p1", "rage", 2, 100)
        ok = world.spend("p1", 2, "r1")
        print("ok=%s rage=%d mana=%d" % (str(ok).lower(),
                                         world.get("p1", "rage"), world.get("p1", "mana")))
    elif args.sample == "rollback":
        world = Pools(order=("rage", "mana"))
        world.set("p1", "rage", 1, 100)
        world.set("p1", "mana", 2, 100)
        ok = world.spend("p1", 5, "r1")
        print("ok=%s rage=%d mana=%d" % (str(ok).lower(),
                                         world.get("p1", "rage"), world.get("p1", "mana")))
    elif args.sample == "cap":
        world = Pools(order=("rage",))
        world.set("p1", "rage", 10, 5)
        print("rage=%d" % world.get("p1", "rage"))
    elif args.sample == "dup":
        world = Pools(order=("rage",))
        world.set("p1", "rage", 10, 100)
        world.spend("p1", 3, "same")
        world.spend("p1", 3, "same")
        print("rage=%d" % world.get("p1", "rage"))
    elif args.sample == "refund":
        world = Pools(order=("rage",))
        world.set("p1", "rage", 10, 100)
        world.spend("p1", 3, "r1")
        world.refund("p1", "r1")
        print("rage=%d" % world.get("p1", "rage"))
    elif args.sample == "scan":
        world = Pools(order=("rage",))
        for index in range(3000):
            world.set("p-%d" % index, "rage", 100, 100)
        for index in range(3000):
            world.spend("p-2999", 1, "r-%d" % index)
        print("scanned=%d" % world.scanned_count())
    else:
        raise SystemExit("需要 --sample order|rollback|cap|dup|refund|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
