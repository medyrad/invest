"""Untrusted content parser. Runs only in a resource-bounded child process."""

import io
import json
import resource
import sys
import warnings

resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


def inspect(data, extension, kind):
    if data.startswith(b"%PDF-"):
        if extension != "pdf" or kind != "document":
            raise ValueError("نوع واقعی و پسوند سازگار نیستند.")
        from pypdf import PdfReader
        from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ValueError("PDF رمزدار پذیرفته نیست.")
        if len(reader.pages) > 500:
            raise ValueError("PDF بیش از ۵۰۰ صفحه است.")
        dangerous = {
            "/JS",
            "/JavaScript",
            "/AA",
            "/OpenAction",
            "/EmbeddedFiles",
            "/EF",
            "/XFA",
            "/RichMedia",
            "/Launch",
            "/SubmitForm",
            "/ImportData",
            "/GoToR",
            "/GoToE",
            "/URI",
            "/Rendition",
            "/Movie",
            "/Sound",
            "/3D",
            "/AcroForm",
        }
        seen = set()
        count = 0

        def walk(obj, depth=0):
            nonlocal count
            count += 1
            if depth > 60 or count > 20000:
                raise ValueError("ساختار PDF از سقف بررسی بیشتر است.")
            if isinstance(obj, IndirectObject):
                ref = (obj.idnum, obj.generation)
                if ref in seen:
                    return
                seen.add(ref)
                obj = obj.get_object()
            if isinstance(obj, DictionaryObject):
                if (
                    set(obj) & dangerous
                    or str(obj.get("/S")) in dangerous
                    or str(obj.get("/Type")) in {"/EmbeddedFile", "/Filespec", "/Action"}
                ):
                    raise ValueError("PDF دارای محتوای فعال یا پیوست است.")
                for value in obj.values():
                    walk(value, depth + 1)
            elif isinstance(obj, ArrayObject):
                for value in obj:
                    walk(value, depth + 1)

        walk(reader.trailer)
        # Inspect all xref objects, including objects not reachable from the current root.
        for generation, entries in reader.xref.items():
            for number in entries:
                if number:
                    walk(IndirectObject(number, generation, reader))
        for number in reader.xref_objStm:
            walk(IndirectObject(number, 0, reader))
        return "application/pdf", None
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = 25_000_000
    warnings.simplefilter("error", Image.DecompressionBombWarning)
    image = Image.open(io.BytesIO(data))
    formats = {"JPEG": {"jpg", "jpeg"}, "PNG": {"png"}, "WEBP": {"webp"}}
    if (
        image.format not in formats
        or extension not in formats[image.format]
        or (kind == "document" and image.format == "WEBP")
    ):
        raise ValueError("نوع واقعی تصویر مجاز نیست یا پسوند همخوان نیست.")
    if image.width * image.height > 25_000_000 or getattr(image, "n_frames", 1) != 1:
        raise ValueError("تصویر متحرک یا بیش از ۲۵ میلیون پیکسل پذیرفته نیست.")
    image.load()
    rgb = image.convert("RGB")
    rgb.info.clear()
    out = io.BytesIO()
    rgb.save(out, format="JPEG", quality=90)
    if out.tell() > 10 * 1048576:
        raise ValueError("مشتق امن تصویر بیش از سقف پردازش است.")
    return "image/jpeg", out.getvalue()


if __name__ == "__main__":
    try:
        data = sys.stdin.buffer.read(20 * 1048576 + 1)
        if len(data) > 20 * 1048576:
            raise ValueError("فایل بیش از سقف بررسی است.")
        mime, derivative = inspect(data, sys.argv[1], sys.argv[2])
        header = json.dumps({"mime": mime}, ensure_ascii=True).encode() + b"\n"
        sys.stdout.buffer.write(header + (derivative or b""))
    except Exception:
        # Never copy parser content/errors into user-visible logs.
        sys.stderr.write("invalid_or_resource_limited_content")
        sys.exit(2)
