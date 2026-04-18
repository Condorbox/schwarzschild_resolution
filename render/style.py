"""
Shared visual style constants.
"""


class STYLE:
    # Reference circles / rings
    PHOTON_SPHERE_COLOR = "#fbbf24"
    PHOTON_SPHERE_LS = "--"
    PHOTON_SPHERE_LABEL = "Photon sphere (1.5 rs)"

    ISCO_COLOR = "#a78bfa"
    ISCO_LS = ":"
    ISCO_LABEL = "ISCO (3.0 rs)"

    # Geodesic path
    TRAJECTORY_COLOR = "#00d4ff"
    TRAJECTORY_LW = 1.5
    TRAJECTORY_ALPHA = 0.9
    TRAJECTORY_LABEL = "Geodesic path"

    # Start / end markers
    START_COLOR = "#39d353"
    END_COLOR = "#f472b6"
    PLUNGE_COLOR = "#ff6b35"

    # Grid / background
    GRID_COLOR = "#333344"
    HORIZON_COLOR = "black"
    HORIZON_EDGE = "#ffffff"

    # Window / panel backgrounds
    UI_BG        = "#0f0f12"   # outermost window
    UI_PANEL_BG  = "#16161a"   # left sidebar
    UI_CARD_BG   = "#1c1c22"   # stat cards / section backgrounds
    UI_BORDER    = "#2a2a35"   # separators and outlines
    UI_CANVAS_BG = "#0a0a0e"   # orbit canvas
 
    # Text
    UI_TEXT       = "#e4e4e7"
    UI_TEXT_MUTED = "#71717a"

    # Accent colours
    UI_ACCENT = TRAJECTORY_COLOR        # "#00d4ff"
    UI_GREEN  = START_COLOR             # "#39d353"
    UI_PINK   = END_COLOR               # "#f472b6"
    UI_ORANGE = PLUNGE_COLOR            # "#ff6b35"
    UI_AMBER  = PHOTON_SPHERE_COLOR     # "#fbbf24"
    UI_PURPLE = ISCO_COLOR              # "#a78bfa"

    # UI Text
    UI_TEXT       = "#e8e8f0"   # primary readable text
    UI_TEXT_MUTED = "#5a5a72"   # secondary / labels
    UI_GRID = "#1a1a24"

    # UI typography
    _F  = "DM Sans"
    _FM = "DM Mono"   # monospaced variant for numeric readouts
 
    FONT_TITLE       = (_F,  13, "bold")
    FONT_SUBTITLE    = (_F,  11)
    FONT_SECTION     = (_F,   9, "bold")
    FONT_LABEL       = (_F,  10)
    FONT_LABEL_BOLD  = (_F,  10, "bold")
    FONT_SMALL       = (_F,   9)
    FONT_STAT_VAL    = (_FM, 14, "bold")   # numeric readout in stat cards
    FONT_STAT_LABEL  = (_F,   8)
    FONT_BTN         = (_F,  11, "bold")
    FONT_RADIO       = (_F,  10)
    FONT_LEGEND      = (_F,   9)
    FONT_CANVAS_TICK = (_FM,  8)           # r-labels on the canvas

