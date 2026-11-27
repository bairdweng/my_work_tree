#!/usr/bin/env python3
"""eBay 定价计算器（美国站 / 包邮 / SpeedPAK）。

两个方向：
  A 成本 → 保底价与目标价      --cost --weight --declared --duty --margin
  B 售价 → 利润               追加 --price

示例：
  python3 price_calc.py --cost 65 --weight 250 --declared 18 --duty 0.25 --margin 0.30
  python3 price_calc.py --cost 65 --weight 250 --declared 18 --duty 0.25 --margin 0.30 --price 39.99
"""
import argparse
import math

FVF = 0.136          # 美国站多数类目（含汽配）
PER_ORDER = 0.40     # 订单 > $10
INTL = 0.0155        # 中国注册地址 → Rest of World 跨国交易费
FX_LOSS = 0.01       # 提现换汇损耗，估算
SPEEDPAK_RATE = 154.50   # 人民币/公斤（2026-06-16 起）
MIN_BILLED_G = 50


def speedpak_cny(weight_g):
    w = max(weight_g, MIN_BILLED_G)
    if w <= 100:
        op = 24.0
    elif w <= 200:
        op = 25.0
    elif w <= 450:
        op = 28.0
    else:
        op = 39.0
    return SPEEDPAK_RATE * w / 1000 + op, op


def money(x):
    return f"${x:,.2f}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cost", type=float, required=True, help="货款+国内运费（人民币）")
    p.add_argument("--weight", type=float, required=True, help="包装后重量（克）")
    p.add_argument("--declared", type=float, required=True, help="申报价（USD）")
    p.add_argument("--duty", type=float, required=True, help="关税率，如 0.25")
    p.add_argument("--margin", type=float, default=0.30, help="目标利润率（占售价），默认 0.30")
    p.add_argument("--price", type=float, help="已定价，反算利润")
    p.add_argument("--fx", type=float, default=7.1, help="人民币/美元，默认 7.1")
    p.add_argument("--tax", type=float, default=0.07, help="买家销售税均值，影响 FVF 基数")
    a = p.parse_args()

    ship_cny, op_fee = speedpak_cny(a.weight)
    cost_usd = a.cost / a.fx
    ship_usd = ship_cny / a.fx
    duty_usd = a.duty * a.declared

    rate = FVF * (1 + a.tax) + INTL + FX_LOSS
    fixed_total = cost_usd + ship_usd + duty_usd + PER_ORDER

    pmin = fixed_total / (1 - rate)
    ptarget = fixed_total / (1 - rate - a.margin) if a.margin < 1 - rate else float("inf")

    print("成本明细")
    print(f"  货款          {money(cost_usd)}   (¥{a.cost:,.2f} / {a.fx})")
    print(f"  物流          {money(ship_usd)}   (¥{ship_cny:,.2f} = {SPEEDPAK_RATE}/kg + 操作费 ¥{op_fee:.0f})")
    print(f"  关税          {money(duty_usd)}   ({a.duty:.0%} × 申报 {money(a.declared)})")
    print(f"  固定费        {money(PER_ORDER)}")
    print(f"  合计          {money(fixed_total)}")
    print()
    print(f"费率           {rate:.2%}  (13.6% 含税 {a.tax:.0%} + 1.55% 跨国 + 1% 汇损)")
    print(f"保底价         {money(pmin)}")
    print(f"目标价({a.margin:.0%})    {money(ptarget)}")
    if ptarget != float("inf"):
        print(f"关税占比       {duty_usd / ptarget:.1%}（按目标价）")
    print()

    start = math.ceil((pmin + 0.01) / 5)
    print("价位敏感度")
    print("  售价      利润      利润率")
    for i in range(6):
        price = (start + i) * 5 - 0.01
        profit = price * (1 - rate) - fixed_total
        print(f"  {money(price):>8}  {money(profit):>8}  {profit / price:>7.1%}")

    if a.price:
        print()
        profit = a.price * (1 - rate) - fixed_total
        print(f"反算：售价 {money(a.price)}")
        print(f"  利润        {money(profit)}")
        print(f"  利润率      {profit / a.price:.1%}")
        if profit < 0:
            print("  结论        亏钱，不成立")
        elif a.price < pmin:
            print("  结论        低于保底价")
        elif profit / a.price < a.margin:
            print(f"  结论        未达 {a.margin:.0%} 目标，可接受则用，否则压成本或提价")
        else:
            print("  结论        达标")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
