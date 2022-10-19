from textwrap import dedent

# distances / mmm
z_retract = 3 # z position while traveling
z_engaged = 0 # z position while cutting
z_final = 10 # final z position

# rates / mm/min
xy_travel = 2100
xy_cut = 720
z_travel = 500
z_cut = 210

tool_change_layers = {2,3} # which layers need a tool change


document_start = f""";Generated with vpype gwrite fabian
G90 ; Use absolute position
G92 X0 Y0 Z0 ; Set the current position as (0,0,0)
G00 X0 Y0 Z{z_retract} F{z_travel}

"""

def layer_join(layer_index, **kwargs):
    # layer index is of the finished layer, not the next one
    note = f"Begin Layer: layer={layer_index+1}"
    tool_change = dedent(
        f"""
        G00 X0 Y0 Z{z_retract} F{xy_travel}
        G01 X0 Y0 Z0 F{z_cut}
        M0 {note}
        G00 X0 Y0 Z{z_retract} F{z_travel}
        """
    )

    if layer_index+1 in tool_change_layers:
        return f";{note}\n{tool_change}\n"
    return f";{note}\n\n"

def segment_first(x, y, layer_index, lines_index, **kwargs):
    return dedent(f"""\
        ;Begin Line: layer={layer_index} line={lines_index}
        G00 X{x:.4f} Y{y:.4f} Z{z_retract}    F{xy_travel}
        G01 X{x:.4f} Y{y:.4f} Z{z_engaged} F{z_cut}
        """
    )

def segment(x, y, **kwargs):
    return f"G01 X{x:.4f} Y{y:.4f} Z{z_engaged} F{xy_cut}\n"

def line_end(x, y, **kwargs): return f"G00 X{x:.4f} Y{y:.4f} Z{z_retract}    F{z_travel}\n\n"

document_end = f"""
G00 X0 Y0 Z{z_retract} F{xy_travel}
G00 X0 Y0 Z{z_final} F{z_travel}
"""

unit = "mm"

vertical_flip = True
