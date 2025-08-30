import staticmaps
import s2sphere
import libsixel
from io import BytesIO
import os
import sys
from contact.utilities.singleton import ui_state
import array
import fcntl
import termios
from PIL import Image
import curses

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


def get_terminal_size():
    """ Get active terminal size in pixels """
    buf = array.array('H', [0, 0, 0, 0])
    fcntl.ioctl(1, termios.TIOCGWINSZ, buf)
    return [buf[2], buf[3]]

def write_sixel(data: bytes):
    """Write raw sixel data directly to the terminal"""
    fd = sys.__stdout__.fileno()
    os.write(fd, data)
    # Flush original stdout to terminal
    os.fsync(fd)

def print_map(stdscr: curses.window) -> None:
    """ Print sixel decoded node map on the screen """

    # Temporary exit curses so we can print the binary sixel data
    curses.endwin()
    # Clear terminal before printing sixel
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

    # Get reminal width and height for printing map fulscreen
    w,h = get_terminal_size()

    # Reduce resolution on half and resampel back to the terminal widht and height
    # This make text more readable and nodes more identifiable
    image = context.render_pillow(int(w/2), int(h/2)).convert('RGB')
    image = image.resize((w, h), Image.Resampling.LANCZOS)
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
            write_sixel(s.getvalue())
        finally:
            libsixel.sixel_dither_unref(dither)
    finally:
        libsixel.sixel_output_unref(output)

    # Find a way to wait for keypress and go back to curses
    # but app also gets update from other place, so I need to figure out where
    # and make some logic so it proceeeds to the other ui only if keypressed
    stdscr.getch()

    # Resume curses
    stdscr.refresh()
    curses.doupdate()

if __name__ == "__main__":
    print_map()
