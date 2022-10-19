gcode input:
    #!/usr/bin/env bash
    set -euxo pipefail
    vpype --config gwrite-fabian.toml \
        read {{input}} \
        linemerge --tolerance 0.1mm \
        linesort \
        reloop \
        linesimplify --tolerance 0.01mm \
        gwrite {{input}}.gcode \
        show

# Example of how to do layout
layout input:
    vpype read {{input}} layout --fit-to-margins 2cm -h center -v center --landscape 9inx6in show

