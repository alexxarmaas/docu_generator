import io

from PIL import Image

from docu_generator.services.image_renderer import render_annotated_image


def _image_bytes() -> bytes:
    image = Image.new("RGB", (400, 240), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_annotations_render_to_png_and_crop_changes_size():
    rendered = render_annotated_image(
        _image_bytes(),
        [
            {
                "id": "r1",
                "type": "rect",
                "x": 0.1,
                "y": 0.1,
                "width": 0.4,
                "height": 0.3,
                "x2": 0,
                "y2": 0,
                "label": "",
                "color": "#00B8A9",
            },
            {
                "id": "n1",
                "type": "number",
                "x": 0.7,
                "y": 0.5,
                "width": 0,
                "height": 0,
                "x2": 0,
                "y2": 0,
                "label": "1",
                "color": "#092D54",
            },
            {
                "id": "b1",
                "type": "blur",
                "x": 0.55,
                "y": 0.1,
                "width": 0.2,
                "height": 0.2,
                "x2": 0,
                "y2": 0,
                "label": "",
                "color": "#E24A4A",
            },
        ],
        {
            "x": 0.05,
            "y": 0.1,
            "width": 0.8,
            "height": 0.7,
        },
    )

    assert rendered.startswith(b"\x89PNG")

    image = Image.open(io.BytesIO(rendered))
    assert image.size == (320, 168)


def test_arrow_annotation_renders_without_crop():
    rendered = render_annotated_image(
        _image_bytes(),
        [
            {
                "id": "a1",
                "type": "arrow",
                "x": 0.1,
                "y": 0.2,
                "x2": 0.8,
                "y2": 0.7,
                "width": 0,
                "height": 0,
                "label": "",
                "color": "#00B8A9",
            }
        ],
    )

    image = Image.open(io.BytesIO(rendered))
    assert image.size == (400, 240)
