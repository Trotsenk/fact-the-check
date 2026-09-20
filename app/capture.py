"""Захват слайда с фото (урок 2б, решение № 32): найти рамку, выпрямить, решить исход."""
import cv2
import numpy as np

# Пороги подобраны на 56 фото Ивана (урок 2б) — проверить на новой партии, не входившей в подбор.
SLIDE_RATIO = (1.25, 1.95)     # выпрямленная рамка: от 4:3 (1,33) до 16:9 (1,78) с запасом на перекос
WHOLE_RATIO = (1.6, 2.2)       # «весь кадр — уже слайд» только для широких кадров: камера телефона снимает 4:3
MIN_SHARE = 0.15               # рамка должна занимать не меньше 15 % кадра


def order_corners(pts):
    """4 угла в любом порядке → верхний левый, верхний правый, нижний правый, нижний левый."""
    pts = pts.astype("float32")
    s = pts.sum(axis=1)                  # x + y: меньше всех у верхнего левого, больше всех у нижнего правого
    d = pts[:, 1] - pts[:, 0]            # y − x: меньше всех у верхнего правого, больше всех у нижнего левого
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype="float32")


def find_frame(photo):
    """Фото → 4 угла самого большого четырёхугольника (≥ 15 % кадра) или None."""
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = gray.shape
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        corners = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(corners) == 4 and cv2.contourArea(corners) / (w * h) > MIN_SHARE:
            return corners.reshape(4, 2)
    return None


def straighten(photo, frame):
    """Фото и 4 угла → выпрямленный прямоугольник."""
    src = order_corners(frame)
    tl, tr, br, bl = src
    out_w = int(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl)))
    out_h = int(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr)))
    dst = np.array([[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]], dtype="float32")
    return cv2.warpPerspective(photo, cv2.getPerspectiveTransform(src, dst), (out_w, out_h))


def ratio_in(img, limits):
    """Лежит ли отношение ширины к высоте картинки в пределах limits = (от, до)."""
    ratio = img.shape[1] / img.shape[0]
    return limits[0] <= ratio <= limits[1]


def capture(photo):
    """Фото → (картинка слайда или None, исход): «рамка», «весь кадр» или «не найдено»."""
    frame = find_frame(photo)
    if frame is not None:
        slide = straighten(photo, frame)
        if ratio_in(slide, SLIDE_RATIO):          # без этой проверки вырезалась таблица внутри слайда
            return slide, "рамка"
    if ratio_in(photo, WHOLE_RATIO):
        return photo, "весь кадр"
    return None, "не найдено"
    