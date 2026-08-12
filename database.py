import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão configurada com o SQLite."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    """Inicializa as tabelas do banco de dados caso não existam."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabela de Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Tabela de Itens da Lista de Desejos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wishlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                url TEXT,
                category TEXT DEFAULT 'Geral',
                status TEXT DEFAULT 'PENDING',
                checkpoint_stage INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_notification_sent_at TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );
        """)
        conn.commit()


def upsert_user(user_id: int, first_name: str) -> None:
    """Registra ou atualiza o nome do usuário."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, first_name)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name;
        """, (user_id, first_name))
        conn.commit()


def create_item(user_id: int, title: str, price: float, url: Optional[str], category: str) -> int:
    """Cria um novo item na lista de desejos e retorna o ID gerado."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wishlist_items (user_id, title, price, url, category, status, checkpoint_stage)
            VALUES (?, ?, ?, ?, ?, 'PENDING', 0);
        """, (user_id, title, price, url, category))
        conn.commit()
        return cursor.lastrowid


def get_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    """Busca um item pelo ID."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM wishlist_items WHERE id = ?;
        """, (item_id,)).fetchone()
        return dict(row) if row else None


def update_item_status(item_id: int, status: str) -> bool:
    """Atualiza o status de um item (PENDING, PURCHASED, CANCELLED, EXPIRED)."""
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE wishlist_items
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (status, item_id))
        conn.commit()
        return cursor.rowcount > 0


def update_item_price(item_id: int, price: float) -> bool:
    """Atualiza o preço de um item."""
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE wishlist_items
            SET price = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (price, item_id))
        conn.commit()
        return cursor.rowcount > 0


def update_item_checkpoint(item_id: int, stage: int) -> bool:
    """Atualiza o estágio do checkpoint de um item."""
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE wishlist_items
            SET checkpoint_stage = ?,
                last_notification_sent_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (stage, item_id))
        conn.commit()
        return cursor.rowcount > 0


def get_active_items_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Retorna os itens pendentes (em resfriamento) de um usuário."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM wishlist_items
            WHERE user_id = ? AND status = 'PENDING'
            ORDER BY created_at DESC;
        """, (user_id,)).fetchall()
        return [dict(row) for row in rows]


def get_all_pending_items() -> List[Dict[str, Any]]:
    """Retorna todos os itens pendentes no sistema."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM wishlist_items
            WHERE status = 'PENDING';
        """).fetchall()
        return [dict(row) for row in rows]


def get_monthly_stats(user_id: int) -> Dict[str, Any]:
    """Calcula as estatísticas consolidadas para os relatórios visuais."""
    with get_connection() as conn:
        # Total economizado (itens cancelados ou expirados)
        saved_row = conn.execute("""
            SELECT COALESCE(SUM(price), 0) as total_saved, COUNT(*) as count_saved
            FROM wishlist_items
            WHERE user_id = ? AND status IN ('CANCELLED', 'EXPIRED');
        """, (user_id,)).fetchone()
        
        total_saved = saved_row["total_saved"] if saved_row else 0.0
        count_saved = saved_row["count_saved"] if saved_row else 0

        # Economizado por Categoria
        cat_rows = conn.execute("""
            SELECT category, SUM(price) as saved_amount, COUNT(*) as count
            FROM wishlist_items
            WHERE user_id = ? AND status IN ('CANCELLED', 'EXPIRED')
            GROUP BY category;
        """, (user_id,)).fetchall()
        
        category_savings = {row["category"]: row["saved_amount"] for row in cat_rows}

        # Contagem por Status
        status_rows = conn.execute("""
            SELECT status, COUNT(*) as count, COALESCE(SUM(price), 0) as total_price
            FROM wishlist_items
            WHERE user_id = ?
            GROUP BY status;
        """, (user_id,)).fetchall()
        
        status_counts = {"PENDING": 0, "PURCHASED": 0, "CANCELLED": 0, "EXPIRED": 0}
        for row in status_rows:
            status_counts[row["status"]] = row["count"]

        total_finished = status_counts["PURCHASED"] + status_counts["CANCELLED"] + status_counts["EXPIRED"]
        cancellation_rate = ((status_counts["CANCELLED"] + status_counts["EXPIRED"]) / total_finished * 100) if total_finished > 0 else 0.0

        return {
            "total_saved": total_saved,
            "count_saved": count_saved,
            "category_savings": category_savings,
            "status_counts": status_counts,
            "cancellation_rate": cancellation_rate,
            "total_items": sum(status_counts.values())
        }
