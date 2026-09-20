"""Настройки проекта: какие модели на каком шаге и сколько они стоят."""

# Цены в долларах за 1 000 000 токенов: (вход, выход).
# Источник — официальная страница цен Anthropic, проверено 19.09.2026.
PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0),
}


def cost_usd(usage, model):
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    price_input_per_million, price_output_per_million = PRICES[model]
    return ((input_tokens*price_input_per_million) + (output_tokens*price_output_per_million))/1_000_000


# Модели на шаге «чтение слайда» — решение № 39. Меняются только записью в журнал.
READ_MODEL_FAST = "claude-haiku-4-5"      # быстрый режим (приоритет): с подсказкой OCR, метка «упрощённое чтение»
READ_MODEL_ACCURATE = "claude-opus-5"     # точный режим — по запросу

