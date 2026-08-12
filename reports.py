import io
import matplotlib
matplotlib.use('Agg')  # Backend não-interativo para servidores/containers
import matplotlib.pyplot as plt
import database as db

# Palette de cores vibrantes para Dark Mode
DARK_BG = "#121216"
SURFACE_BG = "#1e1e24"
TEXT_COLOR = "#f1f1f5"
COLORS = {
    "CANCELLED": "#00e676",   # Verde neon (Economizado)
    "EXPIRED": "#69f0ae",     # Verde claro (Expirado/Economizado)
    "PURCHASED": "#ff5252",   # Vermelho (Comprado)
    "PENDING": "#29b6f6",     # Azul (Em resfriamento)
    "CAT_ACCENT": ["#29b6f6", "#ab47bc", "#ffca28", "#26a69a", "#ff7043", "#78909c"]
}


def generate_monthly_report(user_id: int) -> tuple[io.BytesIO, str]:
    """
    Gera o relatório visual gráfico em Dark Mode e a mensagem em formato Markdown.
    Retorna (image_buffer, formatted_text).
    """
    stats = db.get_monthly_stats(user_id)
    
    total_saved = stats["total_saved"]
    count_saved = stats["count_saved"]
    category_savings = stats["category_savings"]
    status_counts = stats["status_counts"]
    cancellation_rate = stats["cancellation_rate"]
    total_items = stats["total_items"]

    # --- 1. CONSTRUÇÃO DO TEXTO DO RELATÓRIO ---
    text = (
        f"📊 *Relatório de Controle de Impulso*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Total Economizado:* `R$ {total_saved:,.2f}`\n"
        f"❌ *Compras Evitadas:* `{count_saved}` itens\n"
        f"🛒 *Itens Comprados:* `{status_counts['PURCHASED']}` itens\n"
        f"⏳ *Em Resfriamento:* `{status_counts['PENDING']}` itens\n"
        f"🎯 *Taxa de Sucesso (Descarte):* `{cancellation_rate:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Parabéns por exercitar o consumo consciente!_ 🎉"
    ).replace(',', 'X').replace('.', ',').replace('X', '.')

    # --- 2. GERAÇÃO DOS GRÁFICOS COM MATPLOTLIB ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=DARK_BG)
    
    # Estilo dos eixos
    for ax in (ax1, ax2):
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=TEXT_COLOR)
        for spine in ax.spines.values():
            spine.set_color(SURFACE_BG)

    # --- Subplot 1: Gráfico de Rosca (Economia por Categoria) ---
    if category_savings and sum(category_savings.values()) > 0:
        labels = list(category_savings.keys())
        values = list(category_savings.values())
        colors = COLORS["CAT_ACCENT"][:len(labels)]

        wedges, texts, autotexts = ax1.pie(
            values,
            labels=labels,
            autopct='%1.0f%%',
            startangle=140,
            colors=colors,
            pctdistance=0.75,
            textprops=dict(color=TEXT_COLOR, fontsize=9)
        )
        
        for autotext in autotexts:
            autotext.set_color(DARK_BG)
            autotext.set_weight('bold')

        # Desenhar círculo interno para criar efeito de rosca (Donut)
        centre_circle = plt.Circle((0, 0), 0.55, fc=DARK_BG)
        ax1.add_artist(centre_circle)
        ax1.set_title("Economia por Categoria", color=TEXT_COLOR, fontsize=12, pad=12, fontweight='bold')
    else:
        ax1.text(0.5, 0.5, "Sem economias\nregistradas ainda", color=TEXT_COLOR,
                 ha='center', va='center', fontsize=11, style='italic')
        ax1.axis('off')
        ax1.set_title("Economia por Categoria", color=TEXT_COLOR, fontsize=12, pad=12, fontweight='bold')

    # --- Subplot 2: Gráfico de Barras (Status dos Itens) ---
    bar_categories = ['Evitados', 'Comprados', 'Em Aguardo']
    bar_counts = [
        status_counts['CANCELLED'] + status_counts['EXPIRED'],
        status_counts['PURCHASED'],
        status_counts['PENDING']
    ]
    bar_colors = [COLORS['CANCELLED'], COLORS['PURCHASED'], COLORS['PENDING']]

    bars = ax2.bar(bar_categories, bar_counts, color=bar_colors, width=0.55)
    ax2.set_title("Status dos Itens", color=TEXT_COLOR, fontsize=12, pad=12, fontweight='bold')
    ax2.set_ylabel("Quantidade", color=TEXT_COLOR, fontsize=10)
    ax2.grid(axis='y', linestyle='--', alpha=0.2, color=TEXT_COLOR)

    # Rótulo de valores nas barras
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax2.annotate(f'{int(height)}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),  # 3 points vertical offset
                         textcoords="offset points",
                         ha='center', va='bottom',
                         color=TEXT_COLOR, fontweight='bold', fontsize=10)

    plt.tight_layout()

    # Salvar em buffer de memória (BytesIO)
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, facecolor=DARK_BG, edgecolor='none')
    buffer.seek(0)
    plt.close(fig)

    return buffer, text
