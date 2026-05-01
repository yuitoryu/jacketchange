from pathlib import Path

from PIL import Image


class ImageProcessError(Exception):
    """Base error for jacket image processing."""

    pass


class ImageSizeError(ImageProcessError):
    """Raised when an input image has an unsupported aspect ratio."""

    def __init__(self) -> None:
        """Create the image-size error message."""

        self.message = "Image must be square."
        super().__init__(self.message)


class ImageLoadError(ImageProcessError):
    """Raised when Pillow cannot open an input image."""

    def __init__(self, path: Path) -> None:
        """Create an image-load error for a specific input path."""

        self.message = f"Unable to load image: {path}"
        super().__init__(self.message)


def resize(input_path: Path, allow_morphism: bool = False) -> list[Image.Image]:
    """Load an image and resize it into all jacket asset sizes."""

    try:
        img = Image.open(input_path)
    except Exception as exc:
        raise ImageLoadError(input_path) from exc

    resolution = img.size
    if resolution[0] != resolution[1] and not allow_morphism:
        raise ImageSizeError()

    sizes = [300, 676, 108, 128]
    return [img.resize((size, size), Image.Resampling.BICUBIC) for size in sizes]
