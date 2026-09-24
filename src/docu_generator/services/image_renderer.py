from __future__ import annotations

import io
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from docu_generator.models import ImageAnnotation, ImageCrop


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _point(x: float, y: float, width: int, height: int) -> tuple[int, int]:
    return int(_clamp(x) * width), int(_clamp(y) * height)


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def render_annotated_image(
    raw: bytes,
    annotations: list[ImageAnnotation] | list[dict],
    crop: ImageCrop | dict | None = None,
) -> bytes:
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    width, height = image.size
    draw = ImageDraw.Draw(image)

    parsed = [
        item if isinstance(item, ImageAnnotation) else ImageAnnotation.model_validate(item)
        for item in annotations
    ]

    for annotation in parsed:
        color = annotation.color or "#00B8A9"
        stroke = max(2, int(min(width, height) * 0.004))

        if annotation.type in {"rect", "blur"}:
            x1, y1 = _point(annotation.x, annotation.y, width, height)
            x2, y2 = _point(
                annotation.x + annotation.width,
                annotation.y + annotation.height,
                width,
                height,
            )
            left, right = sorted((x1, x2))
            top, bottom = sorted((y1, y2))

            if annotation.type == "blur":
                if right > left and bottom > top:
                    region = image.crop((left, top, right, bottom))
                    radius = max(6, int(min(width, height) * 0.012))
                    region = region.filter(ImageFilter.GaussianBlur(radius=radius))
                    image.paste(region, (left, top))
                    draw = ImageDraw.Draw(image)
                    draw.rounded_rectangle(
                        (left, top, right, bottom),
                        radius=max(4, stroke * 2),
                        outline=color,
                        width=max(1, stroke // 2),
                    )
            else:
                draw.rounded_rectangle(
                    (left, top, right, bottom),
                    radius=max(6, stroke * 3),
                    outline=color,
                    width=stroke,
                )

        elif annotation.type == "arrow":
            x1, y1 = _point(annotation.x, annotation.y, width, height)
            x2, y2 = _point(annotation.x2, annotation.y2, width, height)
            draw.line((x1, y1, x2, y2), fill=color, width=stroke)

            angle = math.atan2(y2 - y1, x2 - x1)
            head = max(12, int(min(width, height) * 0.025))
            spread = math.radians(28)
            left = (
                x2 - head * math.cos(angle - spread),
                y2 - head * math.sin(angle - spread),
            )
            right = (
                x2 - head * math.cos(angle + spread),
                y2 - head * math.sin(angle + spread),
            )
            draw.polygon([(x2, y2), left, right], fill=color)

        elif annotation.type == "number":
            x, y = _point(annotation.x, annotation.y, width, height)
            radius = max(14, int(min(width, height) * 0.022))
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=color,
                outline="white",
                width=max(2, stroke // 2),
            )
            label = annotation.label or "1"
            font = _font(max(14, int(radius * 1.15)))
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                (x - tw / 2, y - th / 2 - bbox[1]),
                label,
                fill="white",
                font=font,
            )

    parsed_crop = None
    if crop is not None:
        parsed_crop = crop if isinstance(crop, ImageCrop) else ImageCrop.model_validate(crop)

    if parsed_crop is not None:
        left = round(_clamp(parsed_crop.x) * width)
        top = round(_clamp(parsed_crop.y) * height)
        right = round(_clamp(parsed_crop.x + parsed_crop.width) * width)
        bottom = round(_clamp(parsed_crop.y + parsed_crop.height) * height)

        if right > left and bottom > top:
            image = image.crop((left, top, right, bottom))

    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()
