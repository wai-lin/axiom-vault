import json, pathlib
from collections import defaultdict
import matplotlib.pyplot as plt

DATA_DIR = pathlib.Path("data")
OUT_DIR = pathlib.Path("round_reports")
OUT_DIR.mkdir(exist_ok=True)

# ────────────────────────────────────────────────────────────────
#  In-memory structures
#     round  -> node -> set(tx_hash)
#     round  -> tx_hash -> earliest_timestamp
# ────────────────────────────────────────────────────────────────
round_node_hashes = defaultdict(lambda: defaultdict(set))
round_hash_earliest = defaultdict(lambda: defaultdict(lambda: float("inf")))

for node_dir in DATA_DIR.iterdir():
    if not node_dir.is_dir():
        continue
    log_file = node_dir / "transactions_log.json"
    if not log_file.exists():
        continue

    with log_file.open() as f:
        records = json.load(f)

    for entry in records:
        rnd = entry["round"]
        node = entry["node_name"]
        for tx_hash, meta in entry["transactions"].items():
            ts = float(meta["timestamp"])
            round_node_hashes[rnd][node].add(tx_hash)
            if ts < round_hash_earliest[rnd][tx_hash]:
                round_hash_earliest[rnd][tx_hash] = ts


# ────────────────────────────────────────────────────────────────
#  Abbreviate hash: 8 head chars + 4 tail chars
# ────────────────────────────────────────────────────────────────
def short(h):
    return f"{h[:8]}…{h[-4:]}"


# ────────────────────────────────────────────────────────────────
#  Generate and render tables per round
# ────────────────────────────────────────────────────────────────
for rnd in sorted(round_node_hashes):
    per_node = round_node_hashes[rnd]
    earliest = round_hash_earliest[rnd]

    canon_hashes = sorted(earliest, key=lambda h: (earliest[h], h))
    label = {h: str(i + 1) for i, h in enumerate(canon_hashes)}
    node_list = sorted(per_node.keys())
    headers = ["label", "hash", "earliest ts"] + node_list

    rows, colours = [], []

    for h in canon_hashes:
        row = [
            label[h],
            short(h),
            f"{earliest[h]:.2f}",
        ]
        col = ["#ffffff", "#ffffff", "#ffffff"]  # white background for meta cols

        for n in node_list:
            owns = h in per_node[n]
            row.append("✔︎" if owns else "✘")
            col.append("#a6f1a6" if owns else "#f7a6a6")

        rows.append(row)
        colours.append(col)

    # ───── render matplotlib table ─────
    col_widths = [0.06, 0.30, 0.18] + [0.10] * len(node_list)
    fig_w = max(8, len(headers) * 1.2)
    fig_h = max(4, len(rows) * 0.6)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    tbl = ax.table(
        cellText=rows,
        colLabels=headers,
        cellColours=colours,
        colWidths=col_widths,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.4)

    ax.set_title(f"Round {rnd} – Tx coverage", fontsize=12)
    plt.tight_layout()

    out = OUT_DIR / f"round_{rnd}.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[✓] saved {out}")
