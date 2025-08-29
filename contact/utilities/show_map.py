import staticmaps
import s2sphere
import libsixel
from io import BytesIO
import os
import sys
from contact.utilities.singleton import ui_state

class TextLabel(staticmaps.Object):
    def __init__(self, latlng: s2sphere.LatLng, text: str) -> None:
        staticmaps.Object.__init__(self)
        self._latlng = latlng
        self._text = text
        self._margin = 8
        self._arrow = 16
        self._font_size = 11

    def latlng(self) -> s2sphere.LatLng:
        return self._latlng

    def bounds(self) -> s2sphere.LatLngRect:
        return s2sphere.LatLngRect.from_point(self._latlng)

    def extra_pixel_bounds(self) -> staticmaps.PixelBoundsT:
        # Guess text extents.
        tw = len(self._text) * self._font_size * 0.5
        th = self._font_size * 1.2
        w = max(self._arrow, tw + 2.0 * self._margin)
        return (int(w / 2.0), int(th + 2.0 * self._margin + self._arrow), int(w / 2), 0)

    def render_pillow(self, renderer: staticmaps.PillowRenderer) -> None:
        x, y = renderer.transformer().ll2pixel(self.latlng())
        x = x + renderer.offset_x()

        left, top, right, bottom = renderer.draw().textbbox((0, 0), self._text)
        th = bottom - top
        tw = right - left
        w = max(self._arrow, tw + 2 * self._margin)
        h = th + 2 * self._margin

        path = [
            (x, y),
            (x + self._arrow / 2, y - self._arrow),
            (x + w / 2, y - self._arrow),
            (x + w / 2, y - self._arrow - h),
            (x - w / 2, y - self._arrow - h),
            (x - w / 2, y - self._arrow),
            (x - self._arrow / 2, y - self._arrow),
        ]

        renderer.draw().polygon(path, fill=(255, 255, 255, 255))
        renderer.draw().line(path, fill=(255, 0, 0, 255))
        renderer.draw().text((x - tw / 2, y - self._arrow - h / 2 - th / 2), self._text, fill=(0, 0, 0, 255))

def print_map() -> None:
    """ Print sixel decoded node map on the screen """

    # Clearing terminal
    os.system('cls' if os.name == 'nt' else 'clear')

    context = staticmaps.Context()
    context.set_tile_provider(staticmaps.tile_provider_OSM)

    latlng_objects = {}

    for node in ui_state.map_positions:
        node_name = node["name"]
        lat = node["positions"][0]
        lng = node["positions"][1]

        # Create the latlng object
        latlng = staticmaps.create_latlng(lat, lng)

        # Store the object in your dictionary with the node's name as the key
        latlng_objects[node_name] = latlng

        # Add the object to the context using the dictionary
        context.add_object(TextLabel(latlng_objects[node_name], node_name))

    # Test node pin
    # node1 = staticmaps.create_latlng(43.943434, 24.090991)
    # context.add_object(TextLabel(node1, "name"))

    # render non-anti-aliased png
    image = context.render_pillow(1000, 500).convert('RGB')
    width, height = image.size

    s = BytesIO()
    data = image.tobytes()

    output = libsixel.sixel_output_new(lambda data, s: s.write(data), s)

    try:
        dither = libsixel.sixel_dither_new(256)
        libsixel.sixel_dither_initialize(dither, data, width, height, libsixel.SIXEL_PIXELFORMAT_RGB888)
        try:
            libsixel.sixel_encode(data, width, height, 1, dither, output)
            # Print the map
            sys.__stdout__.write(s.getvalue().decode('ascii'))
        finally:
            libsixel.sixel_dither_unref(dither)
    finally:
        libsixel.sixel_output_unref(output)

    # Flush original stdout to  to terminal
    sys.__stdout__.flush()

    # try:
    #     if image.mode == 'RGBA':
    #         dither = libsixel.sixel_dither_new(256)
    #         libsixel.sixel_dither_initialize(dither, data, width, height, libsixel.SIXEL_PIXELFORMAT_RGBA8888)
    #     elif image.mode == 'RGB':
    #         dither = libsixel.sixel_dither_new(256)
    #         libsixel.sixel_dither_initialize(dither, data, width, height, libsixel.SIXEL_PIXELFORMAT_RGB888)
    #     elif image.mode == 'P':
    #         palette = image.getpalette()
    #         dither = libsixel.sixel_dither_new(256)
    #         libsixel.sixel_dither_set_palette(dither, palette)
    #         libsixel.sixel_dither_set_pixelformat(dither, libsixel.SIXEL_PIXELFORMAT_PAL8)
    #     elif image.mode == 'L':
    #         dither = libsixel.sixel_dither_get(libsixel.SIXEL_BUILTIN_G8)
    #         libsixel.sixel_dither_set_pixelformat(dither, libsixel.SIXEL_PIXELFORMAT_G8)
    #     elif image.mode == '1':
    #         dither = libsixel.sixel_dither_get(libsixel.SIXEL_BUILTIN_G1)
    #         libsixel.sixel_dither_set_pixelformat(dither, libsixel.SIXEL_PIXELFORMAT_G1)
    #     else:
    #         raise RuntimeError('unexpected image mode')
    #     try:
    #         libsixel.sixel_encode(data, width, height, 1, dither, output)
    #         print(s.getvalue().decode('ascii'))
    #     finally:
    #         libsixel.sixel_dither_unref(dither)
    # finally:
    #     libsixel.sixel_output_unref(output)


if __name__ == "__main__":
    print_map()
