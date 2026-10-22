"""Parsed fonts, kept between calls.

Reading a face with fontTools costs about 100 ms, and every glyph outline and every math
layout needs one. :func:`parsed_font` parses a face once and keeps a few of the most
recently used, keyed by the SHA-256 of the font bytes and the face index, so a face is
parsed again only after it has been evicted.

fontTools tables load lazily and are not safe to touch from two threads at once, so the
font is handed out under a lock for the duration of the ``with`` block. The block is
re-entrant within a thread.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO

from fontTools.ttLib import TTFont

from glyphkit.fonts.models import FontFace

_LIMIT = 8
_lock = threading.RLock()
_fonts: OrderedDict[tuple[str, int], TTFont] = OrderedDict()


@contextmanager
def parsed_font(face: FontFace) -> Iterator[TTFont]:
    """The fontTools font of ``face``, parsed once and shared; do not close it."""
    key = (face.id.fingerprint, face.id.index)
    with _lock:
        font = _fonts.get(key)
        if font is None:
            font = TTFont(BytesIO(face.data), fontNumber=face.id.index, lazy=False)
            _fonts[key] = font
            while len(_fonts) > _LIMIT:
                _fonts.popitem(last=False)[1].close()
        else:
            _fonts.move_to_end(key)
        yield font


def clear_parsed_fonts() -> None:
    """Close and forget every cached font."""
    with _lock:
        while _fonts:
            _fonts.popitem()[1].close()
