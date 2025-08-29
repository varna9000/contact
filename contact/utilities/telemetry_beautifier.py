import datetime
import curses
import pdb
import sys
from contact.utilities.singleton import ui_state

sensors = {
    'temperature': {'icon':'🌡️  ','unit':'°'},
    'relative_humidity': {'icon':'💧','unit':'%'},
    'barometric_pressure': {'icon':'⮇ ','unit': 'hPa'},
    'lux': {'icon':'🔦 ','unit': 'lx'},
    'uv_lux': {'icon':'uv🔦 ','unit': 'lx'},
    'wind_speed': {'icon':'💨 ','unit': 'm/s'},
    'wind_direction': {'icon':'⮆ ','unit': ''},
    'battery_level': {'icon':'🔋 ', 'unit':'%'},
    'voltage': {'icon':'', 'unit':'V'},
    'channel_utilization': {'icon':'ChUtil:', 'unit':'%'},
    'air_util_tx': {'icon':'AirUtil:', 'unit':'%'},
    'uptime_seconds': {'icon':'🆙 ', 'unit':'h'},
    'latitude_i': {'icon':'🌍 ', 'unit':''},
    'longitude_i': {'icon':'', 'unit':''},
    'altitude': {'icon':'⬆️  ', 'unit':'m'},
    'time': {'icon':'🕔 ', 'unit':''}
}


def humanize_wind_direction(degrees):
    """ Convert degrees to Eest-West-Nnoth-Ssouth directions """
    if not 0 <= degrees <= 360:
        return None

    directions = [
        ("N", 337.5, 22.5),
        ("NE", 22.5, 67.5),
        ("E", 67.5, 112.5),
        ("SE", 112.5, 157.5),
        ("S", 157.5, 202.5),
        ("SW", 202.5, 247.5),
        ("W", 247.5, 292.5),
        ("NW", 292.5, 337.5),
    ]

    if degrees >= directions[0][1] or degrees < directions[0][2]:
        return directions[0][0]

    # Check for all other directions
    for direction, lower_bound, upper_bound in directions[1:]:
        if lower_bound <= degrees < upper_bound:
            return direction

    # This part should ideally not be reached with valid input
    return None

def get_chunks(data: str, node_id: str) -> str:
    """ Breakdown telemetry data and assign emojis for more visual appeal of the payloads """
    reading = data.split('\n')

    # remove empty list lefover from the split
    reading = list(filter(None, reading))
    parsed=""

    temp_latlon = [None, None]

    for item in reading:
        key, value = item.split(":")

        # If value is float, round it to the 1 digit after point
        # else make it int
        if "." in value:
            value = round(float(value.strip()),1)
        else:
            try:
                value = int(value.strip())
            except Exception:
                # Leave it string as last resort
                pass

        match key:
            # convert seconds to hours, for our sanity
            case "uptime_seconds":
                if isinstance(value, (int, float)):
                    value = round(value / 60 / 60, 1)
            # Convert position to degrees (humanize), as per Meshtastic protobuf comment for this telemetry
            # truncate to 6th digit after floating point, which would be still accurate
            case "longitude_i" | "latitude_i":
                value = round(value * 1e-7, 6)
                if key == "latitude_i":
                    temp_latlon[0] = value
                if key == "longitude_i":
                    temp_latlon[1] = value

            # Convert wind direction from degrees to abbreviation
            case "wind_direction":
                value = humanize_wind_direction(value)
            case "time":
                value = datetime.datetime.fromtimestamp(int(value)).strftime("%d.%m.%Y %H:%m")

        if key in sensors:
            parsed+= f"{sensors[key.strip()]['icon']}{value}{sensors[key.strip()]['unit']}  "
        else:
            # just pass through if we haven't added the particular telemetry key:value to the sensor dict
            parsed+=f"{key}:{value}  "

    # Append to positions only if we have position payload and not already in the position list
    if temp_latlon[0] is not None and temp_latlon[1] is not None:
        node_pos = {"name": node_id, "positions": temp_latlon }
        if node_pos not in ui_state.map_positions:
            ui_state.map_positions.append(node_pos)

    return parsed
