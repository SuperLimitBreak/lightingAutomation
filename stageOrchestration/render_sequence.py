import logging
from collections import namedtuple

from calaldees.animation.timeline import Timeline
from stageOrchestration.events.model.triggerline import TriggerLine


log = logging.getLogger(__name__)

RENDER_FUNCTION = 'create_timeline'

RenderedSequence = namedtuple('RenderedSequence', ('timeline', 'triggerline'))


def render_sequence(packer, sequence_module, device_collection, get_time_func, get_media_duration_func, frame_rate=30, timeline=None, triggerline=None):
    """
    Render a lighting sequence to a binary intermediary
    packer is managing/monitoring device_collection -> packer.save saves the frames state
    """
    device_collection.reset()

    timeline = timeline or Timeline()
    triggerline = triggerline or TriggerLine(get_media_duration_func=get_media_duration_func, framerate=frame_rate)
    _render_function = getattr(sequence_module, RENDER_FUNCTION, None)
    if not callable(_render_function):
        log.warning(f'{sequence_module.__name__} does not have {RENDER_FUNCTION} to render a timeline')
        return
    _render_function(device_collection, get_time_func, timeline, triggerline)
    assert timeline.duration, f'{sequence_module.__name__} timeline does not contain any items to animate'

    log.debug(f'Rendering {sequence_module._sequence_name}')
    renderer = timeline.get_renderer()
    frames = int(timeline.duration * frame_rate)
    for timecode in ((frame/frames)*timeline.duration for frame in range(frames+1)):
        renderer.render(timecode)
        packer.save_frame()

    return RenderedSequence(timeline, triggerline)
