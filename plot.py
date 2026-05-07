#!/usr/bin/env python3
"""
plot_rosbag.py
--------------
Lee un rosbag (ROS 1 .bag o ROS 2 .db3/.mcap) y genera tres gráficas:
  1. Posición de ruedas vs tiempo        (/joint_states  → position)
  2. Aceleración lineal vs tiempo        (/imu/data      → linear_acceleration)
  3. Gasto (G_parcial y G_total) vs tiempo (/joint_states → effort)

Gasto parcial en cada instante:
    G_parcial(t) = Σ |F_i(t)|   ∀ joints con esfuerzo no nulo

Gasto total acumulado:
    G_total(t) = ∫₀ᵗ G_parcial(τ) dτ   (integración trapezoidal)

Dependencias (sin instalación ROS):
    pip install rosbags matplotlib numpy

Uso:
    python plot_rosbag.py <ruta_al_bag>
"""

import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")           # sin display; cambia a "TkAgg" si quieres ventana
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

# ── colores ────────────────────────────────────────────────────────────────────
PALETTE = [
    "#00C6FF", "#FF6B6B", "#6BFF91", "#FFD166",
    "#C77DFF", "#FF9F43", "#48CAE4", "#F72585",
]
BG      = "#0D1117"
GRID_C  = "#21262D"
TEXT_C  = "#E6EDF3"
ACCENT  = "#58A6FF"


# ══════════════════════════════════════════════════════════════════════════════
# 1.  LECTURA DEL BAG
# ══════════════════════════════════════════════════════════════════════════════

def read_bag(bag_path: Path):
    """
    Devuelve tres diccionarios con las series temporales extraídas:
        js   → joint_states  {joint_name: {'t', 'pos', 'vel', 'eff'}}
        imu  → {'t', 'ax', 'ay', 'az'}
        cmd  → {'t', 'vx', 'wz'}   (no usado en gráficas pero disponible)
    """
    from rosbags.highlevel import AnyReader
    from rosbags.typesys   import Stores, get_typestore

    typestore = get_typestore(Stores.LATEST)

    js_raw:  dict[str, dict] = {}  # {name: {t, pos, vel, eff}}
    imu_t, imu_ax, imu_ay, imu_az = [], [], [], []
    cmd_t, cmd_vx, cmd_wz         = [], [], []

    with AnyReader([bag_path], default_typestore=typestore) as reader:
        conns_js  = [c for c in reader.connections if c.topic == "/joint_states"]
        conns_imu = [c for c in reader.connections if c.topic == "/imu/data"]
        conns_cmd = [c for c in reader.connections if c.topic == "/cmd_vel"]

        for conn, ts_ns, rawdata in reader.messages(
                connections=conns_js + conns_imu + conns_cmd):

            t_s = ts_ns * 1e-9          # nanosegundos → segundos

            if conn.topic == "/joint_states":
                msg = reader.deserialize(rawdata, conn.msgtype)
                names    = list(msg.name)
                pos_arr  = list(msg.position)
                vel_arr  = list(msg.velocity)
                eff_arr  = list(msg.effort) if len(msg.effort) == len(names) \
                           else [0.0] * len(names)

                for i, name in enumerate(names):
                    if name not in js_raw:
                        js_raw[name] = {"t": [], "pos": [], "vel": [], "eff": []}
                    js_raw[name]["t"].append(t_s)
                    js_raw[name]["pos"].append(pos_arr[i])
                    js_raw[name]["vel"].append(vel_arr[i])
                    js_raw[name]["eff"].append(eff_arr[i])

            elif conn.topic == "/imu/data":
                msg = reader.deserialize(rawdata, conn.msgtype)
                imu_t.append(t_s)
                imu_ax.append(msg.linear_acceleration.x)
                imu_ay.append(msg.linear_acceleration.y)
                imu_az.append(msg.linear_acceleration.z)

            elif conn.topic == "/cmd_vel":
                msg = reader.deserialize(rawdata, conn.msgtype)
                cmd_t.append(t_s)
                cmd_vx.append(msg.linear.x)
                cmd_wz.append(msg.angular.z)

    # Convertir a arrays numpy y normalizar t=0
    t0 = None
    js = {}
    for name, d in js_raw.items():
        ta = np.array(d["t"])
        if t0 is None:
            t0 = ta[0]
        js[name] = {
            "t":   ta - t0,
            "pos": np.array(d["pos"]),
            "vel": np.array(d["vel"]),
            "eff": np.array(d["eff"]),
        }

    imu = {}
    if imu_t:
        ta   = np.array(imu_t)
        if t0 is None:
            t0 = ta[0]
        imu = {
            "t":  ta - t0,
            "ax": np.array(imu_ax),
            "ay": np.array(imu_ay),
            "az": np.array(imu_az),
        }

    return js, imu


# ══════════════════════════════════════════════════════════════════════════════
# 2.  CÁLCULO DEL GASTO
# ══════════════════════════════════════════════════════════════════════════════

def compute_gasto(js: dict, exclude: set = None):
    """
    Interpola todos los joints sobre una grilla temporal común y calcula:
        G_parcial(t) = Σ_i |F_i(t)|
        G_total(t)   = ∫₀ᵗ G_parcial dτ  (trapezoidal)

    exclude: conjunto de nombres de joint a ignorar (p.ej. las ruedas).
    Retorna dict con 't', 'g_parcial', 'g_total'.
    """
    if not js:
        return None

    exclude = exclude or set()
    js_filtered = {k: v for k, v in js.items() if k not in exclude}

    if not js_filtered:
        return None

    # Grilla común (la más densa entre los joints no excluidos)
    all_t = np.concatenate([d["t"] for d in js_filtered.values()])
    t_min, t_max = all_t.min(), all_t.max()
    n_pts = max(len(d["t"]) for d in js_filtered.values())
    t_grid = np.linspace(t_min, t_max, n_pts)

    g_parcial = np.zeros(n_pts)
    for name, d in js_filtered.items():
        # Solo joints con esfuerzo no nulo (involucrados en cinemática)
        if np.all(d["eff"] == 0):
            continue
        f_interp = np.interp(t_grid, d["t"], np.abs(d["eff"]))
        g_parcial += f_interp

    # Integral acumulada (gasto total)
    g_total = np.zeros(n_pts)
    for k in range(1, n_pts):
        dt = t_grid[k] - t_grid[k - 1]
        g_total[k] = g_total[k - 1] + 0.5 * (g_parcial[k] + g_parcial[k - 1]) * dt

    return {"t": t_grid, "g_parcial": g_parcial, "g_total": g_total}


# ══════════════════════════════════════════════════════════════════════════════
# 3.  DETECCIÓN DE JOINTS "RUEDA"
# ══════════════════════════════════════════════════════════════════════════════

def identify_wheels(js: dict):
    """
    Heurística: joints cuya posición varía más de 2π rad probablemente son ruedas.
    Devuelve (wheels, non_wheels).  Si no se detecta ninguna rueda, todos los
    joints se consideran ruedas y non_wheels queda vacío.
    """
    wheels = {
        name: d for name, d in js.items()
        if (d["pos"].max() - d["pos"].min()) > 2 * np.pi
    }
    if not wheels:
        return js, {}
    non_wheels = {name: d for name, d in js.items() if name not in wheels}
    return wheels, non_wheels


# ══════════════════════════════════════════════════════════════════════════════
# 4.  FIGURA
# ══════════════════════════════════════════════════════════════════════════════

def make_figure(js, imu, gasto, out_path):
    fig = plt.figure(figsize=(16, 14), facecolor=BG)
    fig.suptitle(
        "Análisis de Simulación — Pick & Place",
        fontsize=18, fontweight="bold", color=TEXT_C, y=0.97
    )

    gs = gridspec.GridSpec(
        3, 1, figure=fig,
        hspace=0.45, left=0.07, right=0.97, top=0.92, bottom=0.06
    )

    axes = [fig.add_subplot(gs[i]) for i in range(3)]

    def style_ax(ax, title, xlabel, ylabel):
        ax.set_facecolor(BG)
        ax.set_title(title, color=TEXT_C, fontsize=13, fontweight="bold", pad=8)
        ax.set_xlabel(xlabel, color=TEXT_C, fontsize=10)
        ax.set_ylabel(ylabel, color=TEXT_C, fontsize=10)
        ax.tick_params(colors=TEXT_C, labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_C)
        ax.grid(True, color=GRID_C, linewidth=0.8, linestyle="--", alpha=0.7)

    # ── Gráfica 1: Posición de ruedas ─────────────────────────────────────────
    ax1 = axes[0]
    style_ax(ax1, "Posición de Ruedas vs Tiempo", "Tiempo (s)", "Posición (rad)")

    wheels, _ = identify_wheels(js)
    for idx, (name, d) in enumerate(wheels.items()):
        color = PALETTE[idx % len(PALETTE)]
        ax1.plot(d["t"], d["pos"], color=color, linewidth=1.4,
                 label=name, alpha=0.92)
    ax1.legend(
        loc="upper right", facecolor="#161B22", edgecolor=GRID_C,
        labelcolor=TEXT_C, fontsize=8, ncol=min(4, len(wheels))
    )

    # ── Gráfica 2: Aceleración IMU ────────────────────────────────────────────
    ax2 = axes[1]
    style_ax(ax2, "Aceleración Lineal vs Tiempo (IMU)", "Tiempo (s)", "Aceleración (m/s²)")

    if imu:
        for axis_key, label, color in zip(
                ["ax", "ay", "az"],
                ["Acel. X", "Acel. Y", "Acel. Z"],
                [PALETTE[0], PALETTE[1], PALETTE[2]]):
            ax2.plot(imu["t"], imu[axis_key], color=color, linewidth=1.3,
                     label=label, alpha=0.9)
        ax2.legend(
            facecolor="#161B22", edgecolor=GRID_C,
            labelcolor=TEXT_C, fontsize=9
        )
    else:
        ax2.text(0.5, 0.5, "Sin datos de IMU", transform=ax2.transAxes,
                 ha="center", va="center", color=TEXT_C, fontsize=12)

    # ── Gráfica 3: Gasto ──────────────────────────────────────────────────────
    ax3 = axes[2]
    style_ax(ax3, "Gasto Energético vs Tiempo", "Tiempo (s)", "Gasto")

    if gasto is not None:
        ax3.fill_between(gasto["t"], gasto["g_parcial"],
                         alpha=0.25, color=PALETTE[3])
        ax3.plot(gasto["t"], gasto["g_parcial"],
                 color=PALETTE[3], linewidth=1.4,
                 label=r"$G_{parcial}(t) = \sum_i\,|F_i(t)|$")

        ax3_r = ax3.twinx()
        ax3_r.set_facecolor(BG)
        ax3_r.tick_params(colors=TEXT_C, labelsize=9)
        ax3_r.set_ylabel("Gasto Total Acumulado", color=PALETTE[0], fontsize=10)
        ax3_r.plot(gasto["t"], gasto["g_total"],
                   color=PALETTE[0], linewidth=2.0, linestyle="--",
                   label=r"$G_{total}(t) = \int_0^t G_{parcial}\,d\tau$")
        ax3_r.yaxis.label.set_color(PALETTE[0])
        ax3_r.spines["right"].set_edgecolor(PALETTE[0])

        # Leyenda combinada
        lines1, labs1 = ax3.get_legend_handles_labels()
        lines2, labs2 = ax3_r.get_legend_handles_labels()
        ax3.legend(
            lines1 + lines2, labs1 + labs2,
            facecolor="#161B22", edgecolor=GRID_C,
            labelcolor=TEXT_C, fontsize=9, loc="upper left"
        )

        # Anotación del gasto total final
        g_fin = gasto["g_total"][-1]
        ax3_r.annotate(
            f"G_total = {g_fin:.2f}",
            xy=(gasto["t"][-1], g_fin),
            xytext=(-70, -20), textcoords="offset points",
            color=PALETTE[0], fontsize=9,
            arrowprops=dict(arrowstyle="->", color=PALETTE[0], lw=1.2)
        )
    else:
        ax3.text(0.5, 0.5, "Sin datos de effort en joint_states",
                 transform=ax3.transAxes,
                 ha="center", va="center", color=TEXT_C, fontsize=12)

    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"[✓] Figura guardada en: {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# 5.  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Genera gráficas de análisis desde un rosbag."
    )
    parser.add_argument("bag", help="Ruta al archivo .bag / .db3 / .mcap")
    parser.add_argument(
        "-o", "--output", default="robot_analysis.png",
        help="Nombre del archivo de salida (default: robot_analysis.png)"
    )
    args = parser.parse_args()

    bag_path = Path(args.bag)
    if not bag_path.exists():
        sys.exit(f"[✗] No se encontró el archivo: {bag_path}")

    print(f"[…] Leyendo bag: {bag_path}")
    js, imu = read_bag(bag_path)

    print(f"[i] Joints encontrados: {list(js.keys())}")
    print(f"[i] Muestras IMU:       {len(imu.get('t', []))}")

    wheels, non_wheels = identify_wheels(js)
    wheel_names = set(wheels.keys())
    print(f"[i] Ruedas detectadas (excluidas del gasto): {list(wheel_names)}")
    print(f"[i] Joints en gasto: {list(non_wheels.keys()) or list(js.keys())}")

    gasto = compute_gasto(js, exclude=wheel_names)
    if gasto is not None:
        print(f"[i] Gasto total final: {gasto['g_total'][-1]:.4f}")

    out = Path(args.output)
    make_figure(js, imu, gasto, out)


if __name__ == "__main__":
    main()