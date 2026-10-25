# English redraw spec for sprite textures (upright coordinates, see tools/redraw.py)

EDITS = [
    # ---- spr_card #0: card statistics labels (white gothic, no outline)
    dict(set="spr_card", tex=0, box=(41, 0, 104, 16), clear=(41, 0, 104, 16), text="Matches", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(105, 0, 117, 16), text="x", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(41, 16, 90, 31), text="Exp", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(93, 16, 126, 31), text="Win%", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(41, 32, 90, 47), text="Games", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(93, 32, 125, 47), text="Gms", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(41, 48, 88, 63), text="Wins", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(89, 48, 119, 63), text="W-L", outline=None, max_h=12),
    dict(set="spr_card", tex=0, box=(69, 64, 110, 81), text="Uses", outline=None, max_h=12),

    # ---- spr_comm #2: VF.NET rival bookmark hint, followed by the P+K+G buttons
    dict(set="spr_comm", tex=2, box=(0, 0, 112, 16), clear=(0, 0, 113, 32), text="Bookmark this"),
    dict(set="spr_comm", tex=2, box=(0, 16, 112, 32), clear=(0, 16, 1, 17), text="rival with"),

    # ---- spr_sel_ft #0: card update mode caption (the カ->ド card icons are replaced too)
    dict(set="spr_sel_ft", tex=0, box=(197, 180, 351, 195), text="CARD UPDATE MODE", fill=(245, 225, 245), outline=None),

    # ---- spr_chlg #14: route selection instruction (3 lines)
    dict(set="spr_chlg", tex=14, box=(1, 1, 104, 18), clear=(0, 0, 104, 54), text="Lever up/down:"),
    dict(set="spr_chlg", tex=14, box=(1, 18, 104, 36), clear=(0, 18, 1, 19), text="choose your"),
    dict(set="spr_chlg", tex=14, box=(1, 36, 104, 54), clear=(0, 36, 1, 37), text="next route"),

    # ---- spr_chlg #12: "ルート選択" title glyphs -> ROUTE / SELECT (other glyphs blanked)
    dict(set="spr_chlg", tex=12, box=(2, 169, 70, 229), text="ROUTE", shear=0.15),
    dict(set="spr_chlg", tex=12, box=(73, 169, 140, 229), text="SELECT", shear=0.15),
    dict(set="spr_chlg", tex=12, box=(171, 121, 216, 166), text=" "),
    dict(set="spr_chlg", tex=12, box=(181, 1, 249, 61), text=" "),
    dict(set="spr_chlg", tex=12, box=(12, 2, 50, 20), bg=True, text="ROUTE"),
    dict(set="spr_chlg", tex=12, box=(100, 2, 150, 20), bg=True, text="SELECT"),
    dict(set="spr_chlg", tex=12, box=(64, 21, 152, 41), text=" "),
    dict(set="spr_chlg", tex=12, box=(56, 8, 99, 14), bg=True, text=" "),      # long dash (ー) on its bar   # lower bars carry only 選/択: removed

    # ---- spr_game #2: champion / challenger phrases (white gothic, black outline)
    dict(set="spr_game", tex=2, box=(0, 0, 50, 16), text="Beat him!", max_h=13),
    dict(set="spr_game", tex=2, box=(50, 0, 232, 16), text="Challenge the Champion!", max_h=13),
    dict(set="spr_game", tex=2, box=(0, 16, 180, 32), text="If not you, then who?", max_h=13),
    dict(set="spr_game", tex=2, box=(180, 16, 232, 32), text="Rival", max_h=13),
    dict(set="spr_game", tex=2, box=(0, 32, 162, 48), text="Stop the win streak!", max_h=13),
    dict(set="spr_game", tex=2, box=(162, 32, 223, 48), text="Now on a", max_h=13),
    dict(set="spr_game", tex=2, box=(79, 48, 231, 64), text="No one can stop him!", max_h=13),
    dict(set="spr_game", tex=2, box=(0, 64, 75, 80), text="win streak", max_h=13),
    dict(set="spr_game", tex=2, box=(75, 64, 208, 80), text="An unbeaten legend!", max_h=13),

    # ---- spr_game #94: 壱 弐 参 -> 1 2 3 (brush serif)
    dict(set="spr_game", tex=94, box=(74, 4, 92, 22), text="1", font="serif"),
    dict(set="spr_game", tex=94, box=(74, 24, 92, 46), text="2", font="serif"),
    dict(set="spr_game", tex=94, box=(97, 4, 115, 22), text="3", font="serif"),

    # ---- spr_game #97 / #98: network status (crisp + glowing copies)
    dict(set="spr_game", tex=97, box=(10, 8, 80, 24), text="Connected", outline=None),
    dict(set="spr_game", tex=97, box=(14, 40, 76, 57), text="Connected", outline=None, blur=1.2),
    dict(set="spr_game", tex=97, box=(52, 70, 124, 94), text="Failed", outline=None),
    dict(set="spr_game", tex=98, box=(18, 8, 70, 24), text="Busy", outline=None),
    dict(set="spr_game", tex=98, box=(22, 40, 66, 57), text="Busy", outline=None, blur=1.2),

    # ---- spr_staff #2: font trademark line (regular weight)
    dict(set="spr_staff", tex=2, box=(0, 120, 384, 140), text="DynaFont is a registered trademark of DynaLab Inc.",
         font="sansreg", outline=None, align="left"),
]
