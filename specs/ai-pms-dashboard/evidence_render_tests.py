"""Retain full WBS/action renderer coverage after the default became a small overview.

These scenarios exercise the detailed evidence renderers, not default-page acceptance.
Default projection contracts are checked separately in check_human_view.py and browsers.
"""


def evidence_render_script(script):
    initialization = 'renderPortfolio();renderDetail();initializeLive();'
    assert initialization in script
    return script.replace(initialization,
                          'renderPhaseFlow=humanBasePhaseFlow;renderDetail=humanBaseDetail;'
                          'renderShared=humanBaseShared;' + initialization)
