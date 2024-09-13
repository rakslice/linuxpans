#!/bin/bash
"exec" "$(dirname $(readlink -f $0))/linuxpans_virtualenv/bin/python" "$0" "$@"

import argparse

import pulsectl


def parse_args():
    parser = argparse.ArgumentParser(description="A utility to do pans of linux audio apps")

    parser.add_argument("--process", "-P",
                        help="name of the executable to pan audio streams of")

    parser.add_argument("--index", "-i",
                        metavar="N",
                        type=int,
                        help="After finding processes, take the Nth match (0-based index)")

    parser.add_argument("--pid",
                        help="Find the process with id PID",
                        metavar="PID",
                        type=int)

    op_group = parser.add_mutually_exclusive_group()
    op_group.add_argument("--pan", "-p",
                        help="Pan the audio to POS (-1.0 [left] to 1.0 [right])",
                        type=float,
                        metavar="POS")
    op_group.add_argument("--left",
                          help="Pan the audio to the left",
                          dest="pan",
                          action="store_const",
                          const=-1.0)
    op_group.add_argument("--right",
                          help="Pan the audio to the right",
                          dest="pan",
			  action="store_const",
			  const=1.0)
    op_group.add_argument("--center",
                          help="Pan the audio to the center",
                          dest="pan",
                          action="store_const",
                          const=0.0)
    parser.add_argument("--dump", "-d",
                        help="dump proplist for the selected items",
                        default=False,
                        action="store_true")

    return parser.parse_args()


def convert_pan_to_channel_levels(pan):
    """
    Convert the pan to channel level values
    :type pan: float
    :param pan: [-1.0 .. 1.0]
    """
    # 1.0 =>  (0, 1)
    # 0.5 =>  (0.5, 1)
    # 0.20 => (0.8, 1)
    # 0.0 =>  (1, 1)
    # -0.5 => (1, 0.5)
    # -1.0 => (1, 0)

    other_channel_level = 1.0 - abs(pan)
    if pan < 0:
        return 1.0, other_channel_level
    else:
        return other_channel_level, 1.0


def text_match(expected, actual):
    return expected.lower() == actual.lower()


def get_bin_name(item):
    appname = item.proplist.get('application.process.binary')
    if appname is None:
        appname = item.proplist.get('application.id')
    return appname


def get_streams(pulse, process=None, pid=None):
    for item in pulse.sink_input_list():
        #print("")
        #for key, value in item.proplist.items():
        #    print(key, " = ", value)
        appname = get_bin_name(item)
        if appname is None:
            continue
        if process is not None and not text_match(process, appname):
            continue
        if pid is not None and pid != int(item.proplist['application.process.id']):
            continue
        yield item


def main():
    options = parse_args() 

    # FIXME properly validate options here
    if options.pan is not None:
        assert -1.0 <= options.pan <= 1.0

    pulse = pulsectl.Pulse('pan')

    for i, item in enumerate(get_streams(pulse, options.process, options.pid)):
        if options.index is not None and options.index != i: continue
        pl = item.proplist
        print ((u"#%d %s %d '%s'" % (i, get_bin_name(item), int(pl.get('application.process.id', -1)), pl['media.name'])).encode("utf-8"))
        print (item.volume)
        if options.pan is not None:
            assert len(item.volume.values) == 2, "item does not have 2 channels; can't pan"
            left_channel_level, right_channel_level = convert_pan_to_channel_levels(options.pan)
            # Because PulseAudio channel and app volumes are in global terms,
            # we can't just set a channel to 1.0, we need to scale them to the
            # existing highest channel
            cur_max_vol = max(item.volume.values)
            left_channel_level *= cur_max_vol
            right_channel_level *= cur_max_vol
            print ("setting volume to %r" % ([left_channel_level, right_channel_level],))
            new_volume = pulsectl.PulseVolumeInfo([left_channel_level, right_channel_level])
            pulse.volume_set(item, new_volume)

        if options.dump:
            print (pl)


if __name__ == "__main__":
    main()

