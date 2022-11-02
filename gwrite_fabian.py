from textwrap import dedent

# distances / mmm
z_retract = 3 # z position while traveling
z_engaged = 0 # z position while cutting
z_final = 10 # final z position

fmt = "0>8.4f"

# rates / mm/min
xy_travel = 2100
xy_cut = 720
# xy_cut = 360
z_travel = 500
z_cut = 210


tool_change_layers = [] # which layers need a tool change


document_start = f""";Generated with vpype gwrite fabian
G90 ; Use absolute position
G92 X0 Y0 Z0 ; Set the current position as (0,0,0)
G0   X000.0000   Y000.0000   Z{z_retract:{fmt}}   F{z_travel}

"""

def layer_join(layer_index, **kwargs):
    # layer index is of the finished layer, not the next one
    note = f"Begin Layer: layer={layer_index+1}"
    tool_change = dedent(
        f"""
        G0   X000.0000   Y000.0000   Z{z_retract:{fmt}}   F{xy_travel}
        G0   X000.0000   Y000.0000   Z000.0000   F{z_cut}
        M0 {note}
        G0   X000.0000   Y000.0000   Z{z_retract:{fmt}}   F{z_travel}
        """
    )

    if layer_index+1 in tool_change_layers:
        return f";{note}\n{tool_change}\n"
    return f";{note}\n\n"

def segment_first(x, y, layer_index, lines_index, **kwargs):
    return dedent(f"""\
        ;Begin Line: layer={layer_index} line={lines_index}
        G0   X{x:{fmt}}   Y{y:{fmt}}   Z{z_retract:{fmt}}   F{xy_travel}
        G0   X{x:{fmt}}   Y{y:{fmt}}   Z{z_engaged:{fmt}}   F{z_cut}
        """
    )

def segment(x, y, **kwargs):
    return f"G0   X{x:{fmt}}   Y{y:{fmt}}   Z{z_engaged:{fmt}}   F{xy_cut}\n"

def line_end(x, y, **kwargs):
    return f"G0   X{x:{fmt}}   Y{y:{fmt}}   Z{z_retract:{fmt}}   F{z_travel}\n\n"

document_end = f"""
G0   X000.0000   Y000.0000   Z{z_retract:{fmt}}   F{xy_travel}
G0   X000.0000   Y000.0000   Z{z_final:{fmt}}   F{z_travel}
"""

unit = "mm"

vertical_flip = True
