revision: str = '245b323e7838'
down_revision = "a59b8f8dfa31"  # замените на фактический ID предыдущей ревизии
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from alembic import op
import sqlalchemy as sa


# Шаги миграции
def upgrade():
    # 1. Создайте временную таблицу с новой структурой
    op.create_table(
        'learned_words_temp',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('word', sa.String, nullable=False),
        sa.Column('translation', sa.String, nullable=False),  # translation теперь NOT NULL
        sa.Column('topic', sa.String),  # Добавление колонки topic
    )

    # 2. Перенесите данные из старой таблицы
    op.execute(
        """
        INSERT INTO learned_words_temp (id, user_id, word, translation, topic)
        SELECT id, user_id, word, translation, NULL FROM learned_words
        """
    )

    # 3. Удалите старую таблицу
    op.drop_table('learned_words')

    # 4. Переименуйте новую таблицу
    op.rename_table('learned_words_temp', 'learned_words')


def downgrade():
    # Откат миграции, если потребуется
    op.create_table(
        'learned_words',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('word', sa.String, nullable=False),
        sa.Column('translation', sa.String, nullable=True),  # translation обратно становится nullable
    )

    op.execute(
        """
        INSERT INTO learned_words (id, user_id, word, translation)
        SELECT id, user_id, word, translation FROM learned_words_temp
        """
    )

    op.drop_table('learned_words_temp')
