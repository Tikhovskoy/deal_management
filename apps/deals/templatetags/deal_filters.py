from django import template

register = template.Library()

STAGE_MAPPING = {
    'NEW': 'Новая',
    'PREPARATION': 'Подготовка',
    'PREPAYMENT_INVOICE': 'Счет на предоплату',
    'EXECUTING': 'Выполняется',
    'FINAL_INVOICE': 'Финальный счет',
    'WON': 'Успешно реализована',
    'LOSE': 'Проиграна',
}

@register.filter
def translate_stage(stage_id):
    return STAGE_MAPPING.get(stage_id, stage_id)