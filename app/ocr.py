"""OCR на своём компьютере (RapidOCR): второй канал для чисел (№ 29, № 31) и подсказка с координатами (урок 2)."""
import re

from rapidocr import RapidOCR

engine = RapidOCR()   # модели лежат внутри пакета — ничего не скачивается; загрузка ≈ 0,3 с один раз


def run_ocr(img):
    """Картинка Pillow (RGB) → строки с координатами (в % слайда), множество чисел и текст для поиска."""
    result = engine(img)
    boxes = result.boxes if result.boxes is not None else []   # на пустой картинке OCR не находит ничего
    texts = result.txts or ()
    lines = []
    for box, text in zip(boxes, texts):
        x = round(box[:, 0].mean() / img.width * 100)      # центр строки: среднее x четырёх углов рамки
        y = round(box[:, 1].mean() / img.height * 100)
        lines.append((y, x, text))
    lines.sort()                                            # сверху вниз, затем слева направо
    raw = " ".join(texts)                                   # через пробел — числа соседних строк не слипаются
    numbers = set()
    for token in re.findall(r"\d+(?:[.,]\d+)?", raw):
        numbers.add(float(token.replace(",", ".")))
    return {"lines": lines, "numbers": numbers, "text": raw.lower().replace(" ", "")}


def hint_text(ocr):
    """Строки OCR → текст подсказки для модели: «[x=.. y=..] строка», как читаем страницу."""
    out = []
    for y, x, text in ocr["lines"]:
        out.append(f"[x={x} y={y}] {text}")
    return "\n".join(out)
    